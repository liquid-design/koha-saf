# koha-saf

**Infrastructure as Code voor een volledig geautomatiseerde Koha ILS-installatie op DigitalOcean.**

Koha is een open-source geïntegreerd bibliotheeksysteem (ILS). Dit project automatiseert de volledige lifecycle — van cloudinfrastructuur tot bibliotheeklogica — zonder handmatige stappen via de webinterface.

---

## Inhoud

- [Overzicht](#overzicht)
- [Vereisten](#vereisten)
- [Snel starten](#snel-starten)
- [Architectuur](#architectuur)
- [Terraform](#terraform)
- [Ansible](#ansible)
- [ISBN Scan Applicatie](#isbn-scan-applicatie)
- [Omgevingen en accounts](#omgevingen-en-accounts)
- [Configuratie aanpassen](#configuratie-aanpassen)
- [Troubleshooting](#troubleshooting)

---

## Overzicht

Het project rolt twee identieke omgevingen uit (productie + test) en configureert ze volledig:

- **Terraform** — DigitalOcean Droplets provisioneren
- **Ansible** — OS, Koha, Apache, TLS en bibliotheeklogica configureren
- **Flask ISBN scanner** — webapplicatie voor het inscannen van boeken via ISBN-barcode

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

Lokaal vereist voor de Flask app:

```bash
pip install flask pymarc requests rich
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

```bash
cd ansible
ansible-playbook -i inventory/terraform.py playbooks/01-bootstrap.yml
ansible-playbook -i inventory/terraform.py playbooks/02-koha-install.yml
ansible-playbook -i inventory/terraform.py playbooks/03-koha-apache.yml
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
ansible-playbook -i inventory/terraform.py playbooks/05-koha-config.yml
ansible-playbook -i inventory/terraform.py playbooks/06-koha-postinstall.yml
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml
ansible-playbook -i inventory/terraform.py playbooks/09-koha-tls.yml
```

Alle playbooks zijn idempotent en kunnen opnieuw worden uitgevoerd zonder bijwerkingen.

---

## Architectuur

```
┌─────────────────────────────────────────────────────────┐
│  Laag             Tool              Verantwoordelijkheid │
├─────────────────────────────────────────────────────────┤
│  Infrastructuur   Terraform         Droplets, netwerk    │
│  Configuratie     Ansible           OS, Koha, TLS        │
│  Applicatie       Koha 25.05        Bibliotheeksysteem   │
│  Catalogisering   Flask + pymarc    ISBN → MARCXML       │
└─────────────────────────────────────────────────────────┘
```

**Servers:** Debian 12, 2 vCPU / 2 GB RAM, regio `ams3` (Amsterdam)

**Netwerkflow:**
```
Internet → Apache (poort 443) → Plack (UNIX socket) → Koha
                              ↗
Flask (poort 5000) ──────────
```

**Inventory:** Ansible gebruikt geen statische hosts. `inventory/terraform.py` leest de Terraform state en genereert de inventory dynamisch. Omgevingen worden bepaald door DigitalOcean tags (`prod`, `test`).

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

| # | Playbook | Rollen |
|---|----------|--------|
| 01 | `bootstrap` | `locale_fix`, `system_hardening_users`, `system_apt`, `system_swap`, `koha_persist_facts` |
| 02 | `koha-install` | `koha_repo`, `koha_install` |
| 03 | `koha-apache` | `koha_apache` |
| 04 | `koha-instance` | `koha_instance` |
| 05 | `koha-config` | `koha_config` |
| 06 | `koha-postinstall` | `koha_postinstall_python`, `koha_postinstall_db`, `koha_postinstall_yaml` |
| 07 | `koha-business` | `koha_business_libraries`, `koha_business_patron_categories`, `koha_business_item_types`, `koha_business_authorised_values`, `koha_business_circulation`, `koha_business_sysprefs`, `koha_business_staff`, `koha_business_admin` |
| 08 | `koha-finalize` | `koha_finalize` |
| 09 | `koha-tls` | `koha_apache-tls`, `certbot`, `koha_apache-tls-finalize` |

### Variabelen

Alle aanpasbare waarden staan in `defaults/main.yml` per role. Omgevingsspecifieke waarden staan in `inventory/group_vars/`:

```
group_vars/
├── all/
│   ├── koha.yml      # Koha versie en repository URL
│   └── system.yml    # Swap grootte en swappiness
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
3. koha_apache-tls-finalize → definitieve TLS vhosts + overbodige sites disablen
```

---

## ISBN Scan Applicatie

De Flask applicatie op `https://scan.marxisme.be` maakt het mogelijk om boeken in te scannen met een handscanner en automatisch in Koha te importeren.

### Flow

```
1. Scan ISBN-barcode met handscanner
2. Flask raadpleegt OpenLibrary + Google Books API
3. Boekgegevens worden getoond (titel, auteur, uitgever, taal)
4. Optioneel: categorieën toevoegen of aanpassen
5. Opslaan → MARCXML bestand aangemaakt in /var/lib/koha/bib/uploads/
6. Cron job (elke minuut) importeert XML via stage_file.pl + commit_file.pl
7. Boek verschijnt als catalogusrecord in Koha
```

### Installatie op de server

```bash
# Applicatiemap aanmaken
sudo mkdir -p /opt/isbn-scanner
sudo cp -r python_project/* /opt/isbn-scanner/

# Python omgeving
cd /opt/isbn-scanner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Upload map aanmaken
sudo mkdir -p /var/lib/koha/bib/uploads
sudo chown bib-koha:bib-koha /var/lib/koha/bib/uploads

# Cron job instellen (als bib-koha gebruiker)
sudo crontab -u bib-koha -e
# Voeg toe: * * * * * /var/lib/koha/bib/koha_import_cron.sh

# Flask starten als systemd service
sudo systemctl enable isbn-scanner
sudo systemctl start isbn-scanner
```

### Apache vhost

```bash
# HTTP vhost aanmaken voor certbot challenge
sudo a2enmod proxy proxy_http
sudo cp sites-available/scan.marxisme.be.conf /etc/apache2/sites-available/
sudo a2ensite scan.marxisme.be.conf
sudo systemctl reload apache2

# Certbot certificaat aanvragen
sudo certbot --apache -d scan.marxisme.be

sudo systemctl reload apache2
```

### Projectstructuur

```
python_project/
├── run.py                  # Flask entry point
├── requirements.txt
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── routes.py           # / (scan) en /save (opslaan)
│   └── templates/
│       └── index.html      # Scanformulier
└── isbn_lookup.py          # OpenLibrary + Google Books + MARCXML logica
```

---

## Omgevingen en accounts

| Omgeving | OPAC | Intranet |
|----------|------|----------|
| Productie | https://bib.marxisme.be | https://bib-intra.marxisme.be |
| Test | https://bib-test.marxisme.be | https://bib-test-intra.marxisme.be |
| Scanner | https://scan.marxisme.be | — |

| Username | Naam | Rol |
|----------|------|-----|
| `kohaadmin` | Karl Marx | Superlibrarian |
| `bibliothecaris` | Rosa Luxemburg | Superlibrarian |
| `catalogisator` | Friedrich Engels | Superlibrarian |

> **Let op:** Wachtwoorden zijn hardcoded voor de POC-fase. Migreer naar Ansible Vault voor productie — de Vault server is reeds uitgerold als onderdeel van de homelab stack.

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
# Verwijder commentaar om te activeren
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
    password_hash: "$2a$08$..."  # bcrypt hash
```

Genereer een hash:

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'wachtwoord', bcrypt.gensalt()).decode())"
```

---

## Troubleshooting

**Apache toont default pagina na TLS deploy**

```bash
ls -la /etc/apache2/sites-enabled/
sudo a2dissite bib.conf
sudo a2dissite bib-le-ssl.conf
sudo systemctl reload apache2
```

**Koha webinstaller verschijnt na login**

```bash
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml
```

**Zebra zoekindex leeg**

```bash
sudo koha-rebuild-zebra -f -a -b -v bib
```

**Ansible facts ontbreken**

```bash
cat /etc/ansible/facts.d/koha.fact
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
```

**Nuttige commando's op de server**

```bash
sudo tail -f /var/log/koha/bib/opac-error.log
sudo apachectl configtest
sudo koha-plack --status bib
sudo koha-plack --restart bib
sudo certbot renew --dry-run
```

---

## Roadmap

- [ ] Ansible Vault integratie voor wachtwoorden en API tokens
- [ ] UFW firewall configuratie
- [ ] ISBN scanner als Ansible role
- [ ] Email/SMTP configuratie voor Koha herinneringen
- [ ] Automatische Koha cron jobs (`overdue_notices`, `fines`, `cleanup_database`)
- [ ] MariaDB backup naar DigitalOcean Spaces
- [ ] Z39.50 voor externe catalogusimport

---

## Licentie

MIT