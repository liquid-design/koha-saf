# 24 — Apache & systeem security hardening

> **Status**: geïmplementeerd op test en prod (mei 2026).
> **Hoort bij**: [doc 04 — Ansible roles](./04-ansible-roles.md), [doc 03 — Deploy pipeline](./03-deploy-pipeline.md).

Dit document beschrijft de security-hardening die in mei 2026 is doorgevoerd
op de Koha SAF-installatie. Het bevat het wat, het waarom, hoe te verifiëren,
hoe te rollbacken, en welke bewuste beperkingen geaccepteerd zijn.

---

## 24.1 — Wat is er gedaan?

Vier categorieën wijzigingen, in volgorde van impact:

### 1. Root password lock (`system_hardening_users`)

**Eerder**: een hardcoded plain-text wachtwoord (`TemporaryPassword123!`) werd
elke Ansible-run als root-wachtwoord gezet, met `update_password: always`.

**Nu**: `password_lock: true` op root. Geen wachtwoord-login meer mogelijk via
welk kanaal dan ook (SSH, DigitalOcean web console, lokale tty). Root via
SSH-key blijft mogelijk indien geconfigureerd in `~/.ssh/authorized_keys`
(beheerd door cloud-init / Terraform).

**Recovery routes**:
- Primair: `ansible` user met sudo
- Noodgeval: DigitalOcean recovery boot mode

### 2. Globale TLS-hardening (`apache_hardening` role)

Nieuwe role plaatst en activeert `/etc/apache2/conf-available/ssl-hardening.conf`
met Mozilla intermediate profile:

- TLS 1.2 en 1.3 only (geen 1.0/1.1)
- Alleen AEAD ciphers (GCM, CHACHA20-POLY1305) — geen CBC, ARIA, Camellia
- X25519 als primaire curve, daarna NIST P-256 en P-384
- `SSLHonorCipherOrder off` (client mag kiezen, beter voor mobile)
- `SSLSessionTickets off` (forward secrecy garantie)

Resultaat: TLS-stack reduceert van ~15 ciphers (OpenSSL defaults) naar 6
ciphers in TLS 1.2 + 3 in TLS 1.3.

### 3. Globale security headers (`apache_hardening` role)

`/etc/apache2/conf-available/security-headers.conf` zet voor alle vhosts:

| Header | Waarde |
|---|---|
| Strict-Transport-Security | `max-age=63072000; includeSubDomains` |
| X-Frame-Options | `SAMEORIGIN` |
| X-Content-Type-Options | `nosniff` |
| Referrer-Policy | `strict-origin-when-cross-origin` |
| Permissions-Policy | `camera=(), microphone=(), geolocation=(), interest-cohort=()` |
| Cross-Origin-Opener-Policy | `same-origin` |
| Cross-Origin-Resource-Policy | `same-origin` |

Centraal: voorkomt drift tussen OPAC en intranet templates (eerder had
intranet bv. HSTS zonder `includeSubDomains`, OPAC met).

### 4. Server-header cloaking

Via `lineinfile` op Debian's `/etc/apache2/conf-available/security.conf`:

```apache
ServerTokens Prod      # was: ServerTokens OS
ServerSignature Off    # was: ServerSignature On
```

`Server: Apache/2.4.67 (Debian)` → `Server: Apache`. Maakt het lastiger om
gericht CVE's voor een specifieke Apache-versie te targeten.

**Waarom in security.conf, niet in onze eigen snippet?** `ServerTokens` is
een directive die Apache vroeg in de config-cyclus parsed en de eerste
waarde aanhoudt. Debian's `security.conf` wordt eerder dan onze
`security-headers.conf` geladen (alfabetisch + andere mechanismen) en wint
als beide ze proberen te zetten. Daarom passen we de Debian-file aan.

### 5. Vhost-template refactor

`koha-opac.conf.j2`, `koha-intranet.conf.j2` en `scan-vhost.conf.j2` hebben
geen inline `Header always set` regels meer. Alles komt via de globale
include. De scan-vhost behoudt een **app-specifieke** `Content-Security-Policy`
(strikt — alleen mogelijk omdat de Flask-app zelf-geschreven is en geen
inline JS bevat).

---

## 24.2 — Architectuur na hardening

```
┌─────────────────────────────────────────────────────┐
│ /etc/apache2/conf-enabled/  (globaal, alle vhosts)  │
│                                                     │
│  security.conf          ← ServerTokens Prod         │
│                          ServerSignature Off        │
│  ssl-hardening.conf     ← Mozilla intermediate      │
│  security-headers.conf  ← 7 security headers        │
└─────────────────────────────────────────────────────┘
                          │
                          ↓ Include vóór elke vhost
                          │
┌──────────────────┬─────────────────┬────────────────┐
│ Koha OPAC vhost  │ Koha staff vhost│ Scan vhost     │
│ (bib*.conf)      │ (bib-intra*.conf)│ (scan*.conf)   │
│                  │                  │                │
│ Geen inline      │ Geen inline      │ Geen inline    │
│ Header regels    │ Header regels    │ Header regels  │
│                  │                  │ + eigen CSP    │
└──────────────────┴─────────────────┴────────────────┘
```

**Bron van waarheid**: de Ansible repo. Alle bestanden hierboven worden
beheerd door de `apache_hardening` of `koha_apache-tls-finalize` of
`flask_isbn_app` roles. Handmatige wijzigingen worden bij de volgende
Ansible-run overschreven.

---

## 24.3 — Playbooks

Drie playbooks zijn relevant voor de hardening:

### `09-koha-tls.yml` — first-time deploy
Draait de hele TLS-flow: HTTP-only stubs → certbot → hardening → finale
TLS vhosts. **Alleen** te gebruiken voor een nieuwe deploy waar nog geen
certificaten bestaan. Tijdens uitvoering is er een stub-stadium waarin
de :443 vhost kortstondig niet werkt — dat is acceptabel bij first-time
deploy maar niet bij re-runs op productie.

### `13-koha-hardening.yml` — alleen hardening updates
Draait alleen de `apache_hardening` role. Idempotent, geen impact op
werkende vhosts. **Dit is de playbook om te draaien** als je headers of
TLS-config wilt updaten.

```bash
ansible-playbook -i inventory/terraform.py -l test \
    playbooks/13-koha-hardening.yml --check --diff
ansible-playbook -i inventory/terraform.py -l test \
    playbooks/13-koha-hardening.yml
```

### `14-koha-vhost-templates.yml` — alleen vhost-templates updates
Draait alleen `koha_apache-tls-finalize`. Idempotent, geen downtime-
window. **Dit is de playbook om te draaien** als je de Koha vhost-
templates wilt updaten zonder certbot of stubs.

```bash
ansible-playbook -i inventory/terraform.py -l test \
    playbooks/14-koha-vhost-templates.yml --check --diff
ansible-playbook -i inventory/terraform.py -l test \
    playbooks/14-koha-vhost-templates.yml
```

Voor de scan-app vhost gebruik je gewoon `10-flask-isbn.yml`.

---

## 24.4 — Verificatie

### Headers per host

```bash
for HOST in bib.marxisme.be bib-intra.marxisme.be scan.marxisme.be \
            bib-test.marxisme.be bib-test-intra.marxisme.be scan-test.marxisme.be; do
    echo ""
    echo "=== $HOST ==="
    curl -sI https://$HOST | grep -iE \
        "strict-transport|x-frame|x-content-type|referrer-policy|permissions-policy|cross-origin|content-security|^server"
done
```

**Verwacht per host**:
- 7 standaard headers
- Scan-vhosts: + Content-Security-Policy
- Alle hosts: `Server: Apache` (geen versie)

### Dubbele headers detecteren

```bash
curl -sI https://bib.marxisme.be | awk '{print $1}' | sort | uniq -c | sort -rn | awk '$1 > 1'
```

**Verwacht**: `2 X-Frame-Options:` — dat is de bekende geaccepteerde
duplicate (zie § 24.6).

### TLS-config strikt

```bash
nmap --script ssl-enum-ciphers -p 443 bib.marxisme.be | grep -E "TLSv|ciphers:"
```

**Verwacht**:
- TLSv1.2: 6 ciphers (allemaal AEAD: GCM of CHACHA20-POLY1305)
- TLSv1.3: 3 ciphers (TLS_AES_128_GCM_SHA256, TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256)

### Online scanners

- **SSL Labs**: https://www.ssllabs.com/ssltest/analyze.html?d=bib.marxisme.be
  - Verwacht: A+ (twee aandachtspunten in 24.6 verlagen de score niet)
- **securityheaders.com**: https://securityheaders.com/?q=bib.marxisme.be
  - Verwacht: A (geen A+ vanwege geen CSP en de dubbele X-Frame — beide bewust)
  - Voor scan-app: A+

### Server lock

```bash
ssh ansible@bib.marxisme.be 'sudo passwd -S root'
```

**Verwacht**: `root L ...` (de `L` = Locked).

---

## 24.5 — Rollback

### Alleen Apache-hardening uitschakelen (snel, geen impact op werking)

```bash
ssh ansible@bib.marxisme.be
sudo a2disconf ssl-hardening security-headers
sudo apache2ctl configtest && sudo systemctl reload apache2
```

Headers en strikte TLS-config zijn weg. Apache gebruikt weer system defaults.

### ServerTokens terugzetten

```bash
ssh ansible@bib.marxisme.be
sudo sed -i 's/^ServerTokens Prod/ServerTokens OS/' /etc/apache2/conf-available/security.conf
sudo sed -i 's/^ServerSignature Off/ServerSignature On/' /etc/apache2/conf-available/security.conf
sudo systemctl reload apache2
```

(Bij de volgende Ansible-run wordt het door `apache_hardening` weer
teruggezet — herstel de role-task in dat geval.)

### Root password lock opheffen

Via DigitalOcean web console (de SSH-route gaat niet zonder password):

1. Open DO dashboard → Droplet → Access → Launch Console
2. Inloggen lukt niet zonder wachtwoord. Reboot droplet in recovery mode:
   - Droplet → Recovery → Boot from Recovery ISO
3. In de recovery shell: mount de root partitie en wijzig `/etc/shadow`,
   of run `passwd root` als de mount automatisch is.

Daarna in Ansible:
```yaml
- name: Unlock root password
  ansible.builtin.user:
    name: root
    password_lock: false
```

En verwijder/comment de `password_lock: true` task in
`roles/system_hardening_users/tasks/main.yml`.

---

## 24.6 — Bekende, geaccepteerde beperkingen

### Dubbele `X-Frame-Options: SAMEORIGIN` op Koha vhosts

Koha's Perl-applicatie (`C4::Output`) zet zelf `X-Frame-Options: SAMEORIGIN`
op responses van `/cgi-bin/koha/*` paden. Apache voegt onze globale waarde
toe. Resultaat: twee identieke headers in de response.

**Waarom niet opgelost?**
- `Header always unset X-Frame-Options` werkt **niet** op upstream/Plack
  headers — alleen op Apache's eigen header-table.
- Koha heeft geen syspref (`OPACFrameOptionsHeader` of vergelijkbaar) om
  het uit te zetten.
- Koha patchen zou upgrades breken.

**Impact**: cosmetisch. Browsers respecteren identieke waarden correct, en
SSL Labs of securityheaders verlagen de score niet noemenswaardig.

### Geen Content-Security-Policy voor Koha

Koha heeft veel inline JavaScript en inline event handlers. Een strikte CSP
zou de OPAC en staff interface stuk maken. Een report-only traject met een
endpoint dat overtredingen logt zou theoretisch werken, maar is een apart
project. Voor nu: geen CSP op Koha vhosts.

De scan-app heeft wèl een strikte CSP, omdat die zelf-geschreven is en geen
inline JS bevat.

### Geen Post-Quantum Cryptography (PQC) TLS

`X25519MLKEM768` (hybride post-quantum key exchange) vereist OpenSSL 3.5+.
Debian 12 heeft OpenSSL 3.0. Wacht op upgrade naar Debian 13 (Trixie) of
op een OpenSSL backport.

### Geen HSTS preload

`preload` op `Strict-Transport-Security` is bewust uitgelaten. Eenmaal in
de HSTS-preload-lijst is uitzetten zeer moeilijk (moet aangevraagd worden
bij browser-vendors en kan maanden duren). Activeer pas wanneer je
absoluut zeker bent dat alle subdomains permanent op HTTPS draaien.

### Intranet (`bib-intra.marxisme.be`) is publiek bereikbaar

De staff-login-pagina is open op het internet. Beschermd door Koha's eigen
login + `FailedLoginAttempts` syspref, maar geen Basic Auth of IP-allowlist
ervoor. Dit was buiten scope van deze hardening-ronde.

Toekomstige opties:
- Basic Auth via htpasswd (zoals scan-app)
- IP-allowlist via Apache `Require ip ...`
- WireGuard/Tailscale VPN voor staff

### Geen fail2ban

Brute-force bescherming op SSH en OPAC/staff login zou via fail2ban kunnen.
Aparte role, niet geïmplementeerd in deze ronde.

---

## 24.7 — Veelvoorkomende issues

### "headers not appearing after deploy"

Eerst Apache configtest:
```bash
ssh ansible@<host> 'sudo apache2ctl configtest'
```

Daarna verifieer dat de snippets enabled zijn:
```bash
ssh ansible@<host> 'ls /etc/apache2/conf-enabled/ | grep -E "ssl-hardening|security-headers"'
```

Beide moeten als symlinks staan. Zo niet:
```bash
ssh ansible@<host>
sudo a2enconf ssl-hardening security-headers
sudo systemctl reload apache2
```

### "X-Frame-Options drie keer in response"

Check waar het vandaan komt:
```bash
ssh ansible@<host> 'sudo grep -rni X-Frame-Options /etc/apache2/ /etc/koha/ 2>/dev/null'
```

Verwacht: alleen `security-headers.conf`. Als er meer staat, is er ergens
inline een `Header always set` blijven hangen — vergelijk met de Ansible
templates.

### "dpkg prompt bij Apache-upgrade"

Bij `apt upgrade apache2` kan dpkg vragen:
```
Configuration file '/etc/apache2/conf-available/security.conf'
 ==> Modified (by you or by a script) since installation.
 ==> Package distributor has shipped an updated version.
   What would you like to do about it?
```

Kies **N** ("keep your currently-installed version"). Daarna draai
`13-koha-hardening.yml` om Ansible's waarden te herstellen.

### "ServerTokens lijkt geen effect te hebben"

Wijzigingen in `ServerTokens` of `ServerSignature` werken pas na een
**volledige reload** van Apache. `graceful` reload pakt het meestal op,
maar bij twijfel:
```bash
ssh ansible@<host> 'sudo systemctl restart apache2'
```

---

## 24.8 — Volgende stappen (roadmap)

Niet acuut, wel op het lijstje voor toekomstige hardening-rondes:

1. **Basic Auth of IP-allowlist op intranet** — staff-login dichttimmeren
2. **fail2ban** — brute-force protection
3. **CSP voor Koha** — eerst report-only traject met log-endpoint
4. **PQC TLS** — wacht op Debian Trixie / OpenSSL 3.5
5. **HSTS preload** — alleen overwegen als alle subdomains gegarandeerd
   permanent op HTTPS blijven

---

## 24.9 — Referenties

- Mozilla SSL Configuration Generator: https://ssl-config.mozilla.org/
- securityheaders.com: https://securityheaders.com/
- SSL Labs: https://www.ssllabs.com/ssltest/
- Apache `mod_headers` docs: https://httpd.apache.org/docs/2.4/mod/mod_headers.html
- HSTS preload requirements: https://hstspreload.org/