# koha-saf

**Infrastructure as Code voor een volledig geautomatiseerde Koha ILS-installatie op DigitalOcean.**

Koha is een open-source geïntegreerd bibliotheeksysteem (ILS). Dit project automatiseert de volledige lifecycle — van cloudinfrastructuur tot bibliotheeklogica, ISBN-scanning, security hardening en backups — zonder handmatige stappen via de webinterface.

---

## Inhoud

- [Overzicht](#overzicht)
- [Vereisten](#vereisten)
- [Snel starten](#snel-starten)
- [Architectuur](#architectuur)
- [Terraform](#terraform)
- [Ansible](#ansible)
- [ISBN Scan Applicatie](#isbn-scan-applicatie)
- [Security](#security)
- [Backup](#backup)
- [Omgevingen en accounts](#omgevingen-en-accounts)
- [Configuratie aanpassen](#configuratie-aanpassen)
- [Troubleshooting](#troubleshooting)
- [Documentatie](#documentatie)

---

## Overzicht

Het project rolt twee identieke omgevingen uit (productie + test) en configureert ze volledig:

- **Terraform** — DigitalOcean Droplets provisioneren
- **Ansible** — OS, Koha, Apache, TLS, security hardening, en bibliotheeklogica
- **Flask ISBN scanner** — webapplicatie voor het inscannen van boeken via ISBN-barcode, gedeployed via Ansible
- **Backup** — 3-2-1 strategie met Backblaze B2 (Object Lock) en on-premise NAS

```
handscanner → https://scan.marxisme.be → Flask → MARCXML → Koha
```

De Koha webinstaller wordt volledig omzeild via geautomatiseerde SQL- en YAML-initialisatie.

---

## Vereisten

| Tool | Versie |
|------|--------|
| Terraform | ≥ 1.0 |
| Ansible | ≥ 2.12 |
| Python | ≥ 3.10 |
| DigitalOcean account | — |

**Ansible Vault password file** (`ansible.cfg` verwacht 'm):

```bash
echo "jouw-vault-wachtwoord" > ~/.ansible-vault-pass-koha-saf
chmod 600 ~/.ansible-vault-pass-koha-saf
```

Bekijk vault inhoud:

```bash
cd ansible
ansible-vault view inventory/group_vars/all/vault.yml
```

---

## Snel starten

### 1 — Infrastructuur uitrollen

```bash
cd terraform
terraform init
terraform plan  -var-file=terraform.tfvars -var-file=secrets/secrets.tfvars
terraform apply -var-file=terraform.tfvars -var-file=secrets/secrets.tfvars
```

### 2 — Koha installeren en configureren

Alle 14 playbooks in volgorde — idempotent, opnieuw uitvoerbaar:

```bash
cd ansible

# Basis OS en Koha
ansible-playbook -i inventory/terraform.py playbooks/01-bootstrap.yml
ansible-playbook -i inventory/terraform.py playbooks/02-koha-install.yml
ansible-playbook -i inventory/terraform.py playbooks/03-koha-apache.yml
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
ansible-playbook -i inventory/terraform.py playbooks/05-koha-config.yml
ansible-playbook -i inventory/terraform.py playbooks/06-koha-postinstall.yml
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml

# TLS (HTTP vhosts → certbot → hardening snippets → finale TLS vhosts)
ansible-playbook -i inventory/terraform.py playbooks/09-koha-tls.yml

# Applicatie + tooling
ansible-playbook -i inventory/terraform.py playbooks/10-flask-isbn.yml
ansible-playbook -i inventory/terraform.py playbooks/11-koha-import.yml

# Security (SSH dichttimmeren LAATSTE — eerst checken dat key-based werkt)
ansible-playbook -i inventory/terraform.py playbooks/12-ssh-hardening.yml
```

### 3 — Alleen security-updates (geen full deploy)

Voor het updaten van security headers, TLS-config of vhost-templates op een werkende server:

```bash
# Apache hardening (TLS + security headers + server tokens)
ansible-playbook -i inventory/terraform.py -l test playbooks/13-koha-hardening.yml

# Alleen Koha vhost-templates (zonder certbot dance)
ansible-playbook -i inventory/terraform.py -l test playbooks/14-koha-vhost-templates.yml
```

### 4 — Selectief per omgeving

Gebruik `-l prod` of `-l test` om één omgeving te targetten:

```bash
ansible-playbook -i inventory/terraform.py -l test playbooks/01-bootstrap.yml
```

Doe altijd eerst test, daarna pas prod.

---

## Architectuur

```
┌──────────────────────────────────────────────────────────────┐
│  Laag             Tool              Verantwoordelijkheid     │
├──────────────────────────────────────────────────────────────┤
│  Infrastructuur   Terraform         Droplets, DNS, firewall  │
│  Configuratie     Ansible           OS, Koha, TLS, security  │
│  Applicatie       Koha 25.05        Bibliotheeksysteem       │
│  Catalogisering   Flask + pymarc    ISBN → MARCXML           │
│  Backup           Backblaze B2      3-2-1 strategie + NAS    │
└──────────────────────────────────────────────────────────────┘
```

**Servers:** Debian 12, 2 vCPU / 2 GB RAM, regio `ams3` (Amsterdam)

**Netwerkflow:**
```
Internet → Apache (443, hardened TLS) → Plack (UNIX socket) → Koha
                                      ↗
Flask + gunicorn (5000, Basic Auth) ──
```

**Inventory:** Ansible gebruikt geen statische hosts. `inventory/terraform.py` leest de Terraform state via `terraform output -json` en genereert de inventory dynamisch. Omgevingen worden bepaald door DigitalOcean tags (`prod`, `test`).

---

## Terraform

Terraform is de **single source of truth** voor infrastructuur. Alle hostinformatie — IP-adressen, regio's, tags — is afkomstig uit Terraform en wordt nooit hardcoded in Ansible.

```hcl
# Voorbeeld output (main.tf)
output "droplets" {
  value = {
    for k, d in digitalocean_droplet.droplet : k => {
      name   = d.name
      ip     = d.ipv4_address
      region = d.region
      tags   = d.tags
    }
  }
}
```

Infrastructuur selectief aanpassen of verwijderen:

```bash
terraform state list
terraform destroy \
  -var-file=terraform.tfvars \
  -var-file=secrets/secrets.tfvars \
  -target='digitalocean_droplet.droplet["koha-saf-test"]'
```

---

## Ansible

### Playbook volgorde

| # | Playbook | Belangrijkste rollen |
|---|----------|----------------------|
| 01 | `bootstrap` | `locale_fix`, `system_hardening_users` (root lock), `system_apt`, `system_swap`, `koha_persist_facts` |
| 02 | `koha-install` | `koha_repo`, `koha_install` |
| 03 | `koha-apache` | `koha_apache` |
| 04 | `koha-instance` | `koha_instance` |
| 05 | `koha-config` | `koha_config` |
| 06 | `koha-postinstall` | `koha_postinstall_python`, `koha_postinstall_db`, `koha_postinstall_yaml` |
| 07 | `koha-business` | `koha_languages`, `koha_business_libraries`, `koha_business_patron_categories`, `koha_business_item_types`, `koha_business_authorised_values`, `koha_business_circulation`, `koha_business_sysprefs`, `koha_business_staff`, `koha_business_admin` |
| 08 | `koha-finalize` | `koha_finalize` |
| 09 | `koha-tls` | `koha_apache-tls`, `certbot`, `apache_hardening`, `koha_apache-tls-finalize` |
| 10 | `flask-isbn` | `flask_isbn_app` |
| 11 | `koha-import` | `koha_import_runner` |
| 12 | `ssh-hardening` | `ssh_hardening` |
| 13 | `koha-hardening` | `apache_hardening` (los) |
| 14 | `koha-vhost-templates` | `koha_apache-tls-finalize` (los) |

### Harde volgorde-eisen

- **09 vóór 10**: `flask_isbn_app` heeft een werkend certbot nodig voor `scan.<domain>` en de `bib-koha` user (uit role 04).
- **10 vóór 11**: `koha_import_runner` heeft `/var/lib/koha-staging` nodig (aangemaakt door `flask_isbn_app`).
- **11 vereist Zebra**: de role bootstrapt `koha-zebra@<instance>` en aborteert bij fail.
- **12 als laatste**: SSH password-auth gaat uit. Test eerst dat `ssh -i ~/.ssh/ansible_nopass ansible@<host>` werkt.

### Variabelen

Alle aanpasbare waarden staan in `defaults/main.yml` per role. Omgevingsspecifieke waarden in `inventory/group_vars/`:

```
group_vars/
├── all/
│   ├── koha.yml      # Koha versie en repository URL
│   ├── system.yml    # Swap grootte en swappiness
│   └── vault.yml     # encrypted (Ansible Vault) — htpasswd, SMTP, etc.
├── prod.yml          # Domeinen, instance naam, e-mail (prod)
└── test.yml          # Domeinen, instance naam, e-mail (test)
```

### Facts persistentie

`koha-create` genereert willekeurige databasecredentials. Deze worden uitgelezen uit `koha-conf.xml` en opgeslagen als Ansible local facts in `/etc/ansible/facts.d/koha.fact`. Alle volgende rollen lezen deze via `ansible_local.koha` — zonder hardcoded credentials.

### TLS flow

De volgorde in playbook 09 is kritiek vanwege de ACME HTTP-01 challenge:

```
1. koha_apache-tls          → HTTP vhosts deployen (poort 80 beschikbaar)
2. certbot                  → certificaten aanvragen via Let's Encrypt
3. apache_hardening         → globale TLS-config + security headers snippets
4. koha_apache-tls-finalize → definitieve TLS vhosts + overbodige sites disablen
```

---

## ISBN Scan Applicatie

De Flask applicatie op `https://scan.marxisme.be` maakt het mogelijk om boeken in te scannen met een handscanner en automatisch in Koha te importeren. **Volledig gedeployed via Ansible** — geen handmatige stappen.

### Flow

```
1. Scan ISBN-barcode met handscanner
2. Flask raadpleegt KB-NL, Library of Congress, BnF, Google Books en OpenLibrary
3. Boekgegevens worden getoond (titel, auteur, uitgever, taal)
4. Optioneel: categorieën toevoegen of aanpassen (42-item SAF categorielijst)
5. Opslaan → MARCXML bestand in /var/lib/koha-staging/
6. Systemd path unit triggert stage_file.pl + commit_file.pl (via koha_import_runner)
7. Boek verschijnt als catalogusrecord in Koha
```

### Bronnen voor metadata (merge-volgorde)

KB-NL → LoC → BnF → Google Books → OpenLibrary (eerste niet-leeg per veld). Geoptimaliseerd voor een Nederlandstalige collectie. OCLC Classify is per januari 2024 deprecated en uit de pipeline gehaald.

### Deployment

```bash
ansible-playbook -i inventory/terraform.py playbooks/10-flask-isbn.yml
ansible-playbook -i inventory/terraform.py playbooks/11-koha-import.yml
```

De `flask_isbn_app` role doet alles:

- Python venv + requirements
- Gunicorn als systemd service (`flask-isbn.service`)
- Apache vhost met **Basic Auth** (htpasswd uit vault) + strikte CSP
- Certbot certificaat voor het scan-domein
- Shared `koha-import` group voor bestandsuitwisseling

De `koha_import_runner` role plaatst de systemd path unit die staging-bestanden detecteert en importeert via `koha-stage-marc-import.pl`.

### Vault-variabelen

In `inventory/group_vars/all/vault.yml`:

```yaml
vault_flask_htpasswd_user: saf
vault_flask_htpasswd_hash: "saf:$2y$05$..."  # uit `htpasswd -nbB saf '<pw>'`
vault_koha_smtp_pass_test: "..."
vault_koha_smtp_pass_prod: "..."
```

---

## Security

Apache- en systeem-hardening is geïmplementeerd in mei 2026. Volledige documentatie: [`docs/24-apache-security-hardening.md`](./docs/24-apache-security-hardening.md).

### Wat is gehard

| Onderdeel | Status |
|---|---|
| Root password lock | ✅ |
| SSH password auth uit + `PermitRootLogin prohibit-password` | ✅ |
| TLS Mozilla intermediate profile (alleen AEAD ciphers, X25519) | ✅ |
| 7 security headers globaal (HSTS, X-Frame, X-Content-Type, Referrer-Policy, Permissions-Policy, COOP, CORP) | ✅ |
| `ServerTokens Prod` + `ServerSignature Off` | ✅ |
| CSP op scan-app (Koha kan dit niet i.v.m. inline JS) | ✅ |
| Basic Auth op scan-app via htpasswd uit vault | ✅ |
| CAA records in DNS | ✅ |
| DigitalOcean cloud firewall | ✅ (via Terraform) |

### Wat nog open staat

- Basic Auth of IP-allowlist op `bib-intra.marxisme.be` (staff interface)
- fail2ban voor brute-force bescherming
- Content-Security-Policy voor Koha (vereist report-only traject)
- PQC TLS (`X25519MLKEM768`) — wacht op Debian 13 / OpenSSL 3.5

### Verificatie

```bash
# Headers per host
curl -sI https://bib.marxisme.be | grep -iE \
    "strict-transport|x-frame|x-content-type|referrer-policy|permissions-policy|cross-origin|^server"

# TLS-strikt
nmap --script ssl-enum-ciphers -p 443 bib.marxisme.be | grep -E "TLSv|ciphers:"

# Online:
# https://www.ssllabs.com/ssltest/analyze.html?d=bib.marxisme.be
# https://securityheaders.com/?q=bib.marxisme.be
```

Verwacht: SSL Labs A+, securityheaders A (Koha) of A+ (scan-app).

---

## Backup

3-2-1 strategie, gedocumenteerd in [`docs/20`-`23`](./docs/):

- **Dagelijks** `koha-dump` → Backblaze B2 met Object Lock (Compliance Mode, 30 dagen)
- Write-only credentials op productie-server (aanvaller kan geen backups deleten)
- **On-premise NAS** pull-only met read-only B2 credentials (offline kopie)
- **DigitalOcean weekly snapshot** als derde laag

Implementatie via `koha_backup` Ansible role (zie roadmap).

---

## Omgevingen en accounts

| Omgeving | OPAC | Intranet | Scanner |
|----------|------|----------|---------|
| Productie | https://bib.marxisme.be | https://bib-intra.marxisme.be | https://scan.marxisme.be |
| Test | https://bib-test.marxisme.be | https://bib-test-intra.marxisme.be | https://scan-test.marxisme.be |

| Username | Rol | Notitie |
|----------|-----|---------|
| `kohaadmin` | Superlibrarian | Default admin, wachtwoord roteren voor productie |
| `bibliothecaris` | Superlibrarian | Bcrypt-hash via vault |
| `catalogisator` | Superlibrarian | Bcrypt-hash via vault |

Branch: `SAF`. Patron categorieën: `S` (Medewerker), `A` (Volwassene), `J` (Jeugd). Item type: `BK` (Boek).

---

## Configuratie aanpassen

Alle bibliotheeklogica is aanpasbaar via `defaults/main.yml` per role, zonder code te wijzigen. Na aanpassing:

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml
```

**Nieuwe bibliotheek toevoegen** — `roles/koha_business_libraries/defaults/main.yml`:

```yaml
koha_libraries:
  - code: SAF
    name: Steunpunt Antifascisme
  - code: BRU
    name: Brussel filiaal
```

**Item type activeren** — `roles/koha_business_item_types/defaults/main.yml`:

```yaml
  - code: DVD
    description: DVD
    loan_period: 7
    renewals: 1
    notforloan: 0
```

**Medewerker toevoegen** — `roles/koha_business_staff/defaults/main.yml`:

```yaml
koha_staff_users:
  - username: nieuwemedewerker
    cardnumber: "1003"
    firstname: Voornaam
    surname: Achternaam
    category: S
    branch: SAF
    flags: 1
    password_hash: "{{ vault_staff_pw_nieuwemedewerker }}"
```

Bcrypt-hash genereren en in vault zetten:

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'wachtwoord', bcrypt.gensalt()).decode())"
ansible-vault edit inventory/group_vars/all/vault.yml
# voeg toe: vault_staff_pw_nieuwemedewerker: "$2b$..."
```

---

## Troubleshooting

**Apache toont default pagina na TLS deploy**

Stubs van `koha_apache-tls` worden niet disabled. Draai finalize:

```bash
ansible-playbook -i inventory/terraform.py playbooks/14-koha-vhost-templates.yml
```

**Koha webinstaller verschijnt na login**

```bash
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml
```

**Zebra zoekindex leeg of import faalt zonder duplicate check**

```bash
ssh ansible@bib.marxisme.be 'sudo systemctl status koha-zebra@bib'
sudo koha-rebuild-zebra -f -a -b -v bib
```

`koha_import_runner` aborteert bij draaiende-Zebra-check als hij niet up is.

**Ansible facts ontbreken**

```bash
cat /etc/ansible/facts.d/koha.fact
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
```

**Dubbele X-Frame-Options in response**

Bekende geaccepteerde beperking: Koha's Perl zet zelf de header, Apache voegt onze globale toe. Cosmetisch, geen security-issue. Zie [`docs/24`](./docs/24-apache-security-hardening.md) § 24.6.

**Flask app onbereikbaar na deploy**

```bash
ssh ansible@bib.marxisme.be 'sudo systemctl status flask-isbn'
ssh ansible@bib.marxisme.be 'sudo journalctl -u flask-isbn -n 50'
```

**Nuttige commando's op de server**

```bash
sudo tail -f /var/log/koha/bib/opac-error.log
sudo apache2ctl configtest
sudo koha-plack --status bib
sudo koha-plack --restart bib
sudo systemctl status koha-import-runner.path
sudo certbot renew --dry-run
```

---

## Documentatie

Uitgebreide documentatie staat in [`docs/`](./docs/):

| Doc | Onderwerp |
|---|---|
| `01` | Projectoverzicht |
| `02` | Architectuur |
| `03` | Deploy pipeline |
| `04` | Ansible roles referentie |
| `05` | Configuratie referentie |
| `06` | TLS architectuur |
| `09` | Projectstructuur |
| `10` | Troubleshooting |
| `11`-`16` | Bibliotheek logica (rollen, circulatie, klikpaden, visuele diagrammen) |
| `20`-`23` | Backup strategie, implementatie, restore, verificatie |
| `24` | Apache & systeem security hardening |

---

## Roadmap

- [x] ~~Ansible Vault integratie~~
- [x] ~~ISBN scanner als Ansible role~~
- [x] ~~Email/SMTP configuratie~~
- [x] ~~Apache + systeem security hardening~~
- [x] ~~SSH hardening (password auth uit)~~
- [x] ~~CAA records in DNS~~
- [ ] `koha_backup` Ansible role implementeren (docs 20-23 zijn klaar, role nog niet)
- [ ] Basic Auth of IP-allowlist op staff interface
- [ ] fail2ban voor brute-force bescherming
- [ ] UFW firewall (naast DO cloud firewall)
- [ ] Automatische Koha cron jobs (`overdue_notices`, `fines`, `cleanup_database`)
- [ ] Default biblio_framework seed in Ansible role
- [ ] CSP voor Koha via report-only traject
- [ ] PQC TLS bij Debian 13 / OpenSSL 3.5 upgrade
- [ ] Z39.50 voor externe catalogusimport

---

## Licentie

MIT