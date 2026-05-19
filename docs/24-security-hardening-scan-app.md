# 24. Security hardening Flask ISBN-scan app

Status: feature branch `feature/security-scan-app`, klaar voor test deploy.

Deze doc beschrijft wat er veranderd is en hoe je het in productie krijgt.

## Wat is er veranderd

### 1. Authenticatie (kritiek)

Tot deze branch was `scan.marxisme.be` publiek toegankelijk zonder login.
Iedereen op internet kon ISBN-lookups doen en MARCXML-files in de staging
dir droppen, die vervolgens automatisch geïmporteerd werden in Koha.

Nu: **HTTP Basic Auth op Apache-niveau**. Eén shared account `saf` met
bcrypt-hash, opgeslagen in `/etc/apache2/scan-htpasswd` (owner root, group
www-data, mode 0640). De hash komt uit Ansible vault.

### 2. CSRF-bescherming

Flask-WTF geïntegreerd. Elk POST-formulier (`/lookup`, `/select`, `/save`)
heeft nu een `csrf_token()` hidden field. Zonder geldig token wordt het
verzoek afgewezen met HTTP 400.

Sessie-cookies zijn nu `Secure`, `HttpOnly`, `SameSite=Strict`.

### 3. Input validatie

In `routes.py`:

- ISBN moet matchen op `^\d{9}[\dXx]|\d{13}$` na strippen van streepjes en spaties
- Barcode moet matchen op `^[A-Za-z0-9_-]{1,32}$` — blokkeert path-traversal
  via filename én eventuele MARC-injection via 952$p
- Category moet uit de officiële `CATEGORIES` lijst komen, anders refuse
- Alle vrije-tekst velden (title, subtitle, authors, ...) worden:
  - NFC unicode-genormaliseerd
  - ontdaan van NULL bytes en control chars (behalve \t \n \r)
  - getrunceerd op een sane max lengte

### 4. Rate limiting

Flask-Limiter geïntegreerd. Vooral om de externe SRU-bronnen (KB-NL, BnF,
LoC, ...) te beschermen tegen misbruik via onze server:

- `/lookup` en `/select`: 30 verzoeken per minuut per IP
- `/save`: 10 verzoeken per minuut per IP
- Globale default: 200 per uur per IP

Bij overschrijding: HTTP 429.

`ProxyFix` middleware zorgt dat het echte client-IP gezien wordt, niet
`127.0.0.1` (de Apache reverse proxy). Apache stuurt `X-Forwarded-Proto`
en de standaard `X-Forwarded-For` mee.

### 5. Secret key handling

Vroeger: secret in `.flask_env`, geladen via `EnvironmentFile=`. Dat zet
hem in `/proc/<pid>/environ`, leesbaar voor andere processen in dezelfde
namespace.

Nu: `LoadCredential` mount het secret als read-only file in
`/run/credentials/flask-isbn.service/flask_secret`. Flask leest het via
`FLASK_SECRET_KEY_FILE` env var. Het secret zelf staat **niet** in een
proces-omgeving.

### 6. Security headers (Apache)

Toegevoegd aan `scan-vhost.conf.j2`:

- `Content-Security-Policy`: `default-src 'self'`, geen inline JS toegestaan
- `Permissions-Policy`: camera/microfoon/geolocation expliciet uit
- `Cross-Origin-Opener-Policy` / `Cross-Origin-Resource-Policy`: isolation

Bestaand: HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy.

### 7. systemd hardening (extra)

Aan flask-isbn.service toegevoegd:

- `ProtectClock`, `ProtectHostname`, `ProtectKernelLogs`
- `RestrictNamespaces`, `SystemCallArchitectures=native`
- `RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX`

### 8. SSH hardening (nieuwe rol)

Aparte rol `ssh_hardening` zet:

- `PasswordAuthentication no`
- `PermitRootLogin prohibit-password`
- `KbdInteractiveAuthentication no`
- `MaxAuthTries 4`

In `/etc/ssh/sshd_config.d/99-hardening.conf` met `sshd -t` validatie en
reload (geen restart) zodat lopende sessies overleven.

### 9. Klein

- `debug=True` uit `run.py`, vervangen door `FLASK_DEBUG` env var voor lokale dev
- `gunicorn --forwarded-allow-ips=127.0.0.1` zodat hij de X-Forwarded headers
  van Apache vertrouwt

## Voor je deployt: vault aanpassen

`inventory/group_vars/all/vault.yml` moet uitgebreid worden met:

```yaml
# Basic Auth voor scan.marxisme.be
vault_flask_htpasswd_user: saf
# Hash genereren met:  htpasswd -nbB saf 'kies-een-sterk-wachtwoord'
# Output is een hele regel "saf:$2y$05$...". Die hele regel hieronder plakken.
vault_flask_htpasswd_hash: "saf:$2y$05$REPLACE_ME_MET_ECHTE_HASH"
```

Stappen om de hash te maken:

```bash
# Op je laptop:
sudo apt install apache2-utils   # voor het htpasswd commando
htpasswd -nbB saf 'jouw-wachtwoord-hier'
# Copy de hele output (incl. "saf:") naar vault_flask_htpasswd_hash

# Edit vault:
ansible-vault edit inventory/group_vars/all/vault.yml
```

## Deploy-volgorde

```bash
# 1. Eerst test
ansible-playbook -i inventory/terraform.py -l test playbooks/10-flask-isbn.yml --ask-vault-pass

# 2. SSH hardening — let op pre-flight check (zie playbook header)
ansible-playbook -i inventory/terraform.py -l test playbooks/12-ssh-hardening.yml --ask-vault-pass

# 3. Manuele rooktest op test:
#    - Open https://scan-test.marxisme.be in incognito
#    - Verwacht: Basic Auth prompt
#    - Login met saf + wachtwoord
#    - Verwacht: ISBN scherm
#    - Open DevTools -> Network -> check response headers (CSP, HSTS, etc.)
#    - Scan een ISBN, doorloop volledige flow tot opgeslagen XML
#    - Probeer een POST naar /save zonder csrf_token (curl) -> verwacht 400
#    - Probeer 31 lookups in een minuut -> verwacht 429 op de 31e

# 4. Als test groen: prod
ansible-playbook -i inventory/terraform.py -l prod playbooks/10-flask-isbn.yml --ask-vault-pass
ansible-playbook -i inventory/terraform.py -l prod playbooks/12-ssh-hardening.yml --ask-vault-pass
```

## Wachtwoord wijzigen (later)

```bash
# Op je laptop:
htpasswd -nbB saf 'nieuw-wachtwoord'

# Plak output in vault:
ansible-vault edit inventory/group_vars/all/vault.yml

# Deploy alleen de htpasswd-task:
ansible-playbook -i inventory/terraform.py playbooks/10-flask-isbn.yml --tags htpasswd
```

(Note: voor de `--tags` variant moet je in `tasks/main.yml` de htpasswd-task
nog taggen. Voor nu: gewoon de hele playbook opnieuw draaien, is idempotent.)

## Rollback

Als iets misgaat na deploy:

```bash
git checkout main
ansible-playbook -i inventory/terraform.py -l test playbooks/10-flask-isbn.yml --ask-vault-pass
```

De Flask-secret blijft staan (file wordt niet aangeraakt door rollback),
dus actieve sessies overleven. Wel: oude code kent geen csrf_token en zal
form-submissions zonder problemen accepteren — bewust de tegenovergestelde
kant op.

## Wat NIET in deze branch zit

- **fail2ban**: aanbevolen maar buiten scope. Apart Ansible-rol bij volgende sprint.
- **Per-persoon accounts**: nu één shared `saf` account. Voor 2-3 mensen prima.
  Audit-trail in `/var/log/apache2/scan-access.log` is wel beperkt (één user).
- **Dependency-scanning**: Dependabot op de GitHub-repo aanzetten is een
  losse actie, geen code-wijziging.
- **CSRF op `/manual` GET**: GET-routes hebben per definitie geen CSRF
  nodig; we leiden alleen door naar `/save` waar wel CSRF op zit.
