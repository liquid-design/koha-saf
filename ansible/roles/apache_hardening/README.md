# apache_hardening role

Globale Apache TLS- en security-header-hardening voor alle Koha vhosts
op deze server (OPAC, intranet, en scan-app).

## Wat doet het?

Plaatst twee snippets in `/etc/apache2/conf-available/`:

- **`ssl-hardening.conf`** — Mozilla intermediate TLS-profile (TLS 1.2 + 1.3,
  AEAD ciphers only, X25519 curve voorop). Vervangt de impliciete OpenSSL
  system defaults door een expliciete, getrackde config.
- **`security-headers.conf`** — gedeelde security headers (HSTS,
  X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
  Permissions-Policy, COOP, CORP). Eén plek voor alles dat OPAC + intranet
  gemeen hebben.

Beide worden globaal geactiveerd via `a2enconf`, dus alle vhosts erven
ze automatisch — geen aanpassingen aan individuele vhost-templates nodig
behalve het verwijderen van duplicate headers die er al in stonden.

## Wat doet het NIET?

- **Vhosts aanmaken** — dat blijft koha_apache-tls en koha_apache-tls-finalize
- **Certbot** — aparte role
- **Per-vhost CSP** — staat in de scan-vhost zelf, omdat alleen die strikt
  kan zijn. Koha's eigen CSP zou een apart traject zijn (veel inline JS).
- **HSTS preload** — bewust niet, eenmaal in preload-lijst is uitzetten zeer
  moeilijk.

## Variabelen

| variabele | default | uitleg |
|---|---|---|
| `apache_hardening_tls_profile` | `intermediate` | `intermediate` (TLS 1.2 + 1.3) of `modern` (TLS 1.3 only) |
| `apache_hardening_ssl_conf_path` | `/etc/apache2/conf-available/ssl-hardening.conf` | zelden aanpassen |
| `apache_hardening_headers_conf_path` | `/etc/apache2/conf-available/security-headers.conf` | zelden aanpassen |

## Gebruik

Apart draaien:
```
ansible-playbook -i inventory/terraform.py -l test playbooks/13-koha-hardening.yml
```

Of laat het meedraaien in `09-koha-tls.yml` (zit er nu in, na de finalize).

## Verificatie

Na deploy:
```bash
# 1. Apache draait?
systemctl status apache2

# 2. Snippets geladen?
sudo apache2ctl -t -D DUMP_INCLUDES | grep -E "(ssl-hardening|security-headers)"

# 3. Headers aanwezig?
curl -sI https://bib-test.marxisme.be | grep -iE "strict-transport|x-frame|x-content-type|referrer|permissions"

# 4. TLS-config strikt?
nmap --script ssl-enum-ciphers -p 443 bib-test.marxisme.be
# Verwacht: 6 ciphers in TLS 1.2 (allemaal AEAD), 3 in TLS 1.3.

# 5. SSL Labs:
# https://www.ssllabs.com/ssltest/analyze.html?d=bib-test.marxisme.be
```

## Rollback

Als er iets misgaat:
```bash
sudo a2disconf ssl-hardening security-headers
sudo apache2ctl configtest && sudo systemctl reload apache2
```

Daarna git revert van de commit, of `apache_hardening_tls_profile`
override naar wat ook werkt.
