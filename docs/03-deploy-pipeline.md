# 3. Deploy Pipeline

De volledige installatie bestaat uit twee fasen: infrastructuur (Terraform) en configuratie (Ansible). De Ansible-fase is opgesplitst in **12 genummerde playbooks** die in volgorde uitgevoerd worden. Dit document beschrijft het overzicht; voor de detail-runbook zie doc 00.

---

## 3.1 Fase 1 — Terraform

### Vereisten

- Terraform ≥ 1.0 geïnstalleerd
- DigitalOcean API token in `secrets/secrets.tfvars`
- SSH keys geconfigureerd in `terraform.tfvars`
- Een Ansible-vault-wachtwoord in `~/.ansible-vault-pass-koha-saf` (zie `ansible-vault-setup.md`)

### Uitvoering

```bash
cd terraform
terraform init
terraform plan  -var-file=secrets/secrets.tfvars
terraform apply -var-file=secrets/secrets.tfvars
```

Terraform maakt aan:

- Twee Droplets (prod + test) met Debian 12, type `s-2vcpu-2gb`, regio `ams3`
- Cloud-init script: `ansible`-gebruiker, SSH keys, sudo rechten
- DigitalOcean tags `prod` / `test` — bepalen de Ansible-groep, zie `inventory/terraform.py` regel 96–99
- DigitalOcean backups en monitoring ingeschakeld

---

## 3.2 Fase 2 — Ansible

Alle playbooks worden uitgevoerd vanuit de `ansible/` map. De dynamische inventory `inventory/terraform.py` leest direct uit `terraform output -json`, dus Terraform moet eerst klaar zijn.

```bash
cd ansible
ansible-inventory -i inventory/terraform.py --list   # verificatie
```

### 3.2.1 Overzicht van de 12 playbooks

| # | Playbook | Verantwoordelijkheid | Roles |
|---|----------|----------------------|-------|
| 01 | `01-bootstrap.yml` | Locale, swap, system users, apt, facts-dir | `locale_fix`, `system_hardening_users`, `system_apt`, `system_swap`, `koha_persist_facts` |
| 02 | `02-koha-install.yml` | Koha apt repo + `koha-common` package | `koha_repo`, `koha_install` |
| 03 | `03-koha-apache.yml` | Apache modules, default sites disablen | `koha_apache` |
| 04 | `04-koha-instance.yml` | `koha-create`, Plack enablen, DB facts persisteren | `koha_instance` |
| 05 | `05-koha-config.yml` | Koha-conf.xml + DB facts valideren | `koha_config` |
| 06 | `06-koha-postinstall.yml` | DB structuur, mandatory SQL/YAML, MARC21 | `koha_postinstall_python`, `koha_postinstall_db`, `koha_postinstall_yaml` |
| 07 | `07-koha-business.yml` | Languages, libraries, patron cats, staff, sysprefs | 9 `koha_business_*` roles + `koha_languages` |
| 08 | `08-koha-finalize.yml` | Version syspref, Zebra rebuild, Plack restart | `koha_finalize` |
| 09 | `09-koha-tls.yml` | HTTP vhosts → certbot → TLS vhosts | `koha_apache-tls`, `certbot`, `koha_apache-tls-finalize` |
| 10 | `10-flask-isbn.yml` | Flask ISBN scan-app op `scan.<domain>` | `flask_isbn_app` |
| 11 | `11-koha-import.yml` | Systemd path unit + Zebra bootstrap + ISBN matcher seed | `koha_import_runner` |
| 12 | `12-ssh-hardening.yml` | PasswordAuthentication uit, root key-only | `ssh_hardening` |

Voor wat elke role concreet doet en welke variabelen ze gebruiken, zie doc 04.

### 3.2.2 Harde volgorde-eisen

Sommige playbooks hebben harde dependencies op eerder werk. De playbooks zelf checken dit waar mogelijk (met `assert` op `ansible_local.koha.*`, of met `stat` op vereiste paden), maar bij twijfel volg de volgorde uit §3.2.1.

| Stap | Vereist | Gecontroleerd in |
|------|---------|------------------|
| 05–08 | Koha facts uit stap 04 | `assert` bovenaan elke role, bv. `roles/koha_config/tasks/main.yml` regel 10–18 |
| 07 (sysprefs) | Translation files van `koha_languages` | Volgorde in `playbooks/07-koha-business.yml` zet `koha_languages` als eerste |
| 09 | Apache uit stap 03, instance uit stap 04 | Apache modules ssl/rewrite/headers worden door `koha_apache-tls` zelf enabled |
| 10 | Certbot uit stap 09, `bib-koha` user uit stap 04 | Flask role vraagt zelf cert aan voor `scan.<domain>` |
| 11 | Staging-dir uit stap 10, `stage_file.pl` aanwezig | `roles/koha_import_runner/tasks/main.yml` regel 19–44 fail loud als tools ontbreken |
| 12 | Werkende key-based SSH | `ssh_hardening` valideert via `sshd -t` voordat het reloadt |

### 3.2.3 Kritieke subvolgorde binnen playbook 09

`09-koha-tls.yml` chained drie roles waarvan de volgorde **niet** te veranderen is:

1. `koha_apache-tls` → tijdelijke HTTP-vhosts (DocumentRoot `/var/www/html`) + `meta: flush_handlers`
2. `certbot` → ACME HTTP-01 challenge tegen die tijdelijke vhosts
3. `koha_apache-tls-finalize` → definitieve TLS-vhosts, overbodige sites disablen, Apache reload

Volgorde-detail: zie ook doc 06 (TLS architectuur).

---

## 3.3 Volledige deploy commando's

Volledige eerste-keer deploy van een kale droplet:

```bash
ansible-playbook -i inventory/terraform.py playbooks/01-bootstrap.yml
ansible-playbook -i inventory/terraform.py playbooks/02-koha-install.yml
ansible-playbook -i inventory/terraform.py playbooks/03-koha-apache.yml
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
ansible-playbook -i inventory/terraform.py playbooks/05-koha-config.yml
ansible-playbook -i inventory/terraform.py playbooks/06-koha-postinstall.yml
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml
ansible-playbook -i inventory/terraform.py playbooks/09-koha-tls.yml
ansible-playbook -i inventory/terraform.py playbooks/10-flask-isbn.yml
ansible-playbook -i inventory/terraform.py playbooks/11-koha-import.yml
ansible-playbook -i inventory/terraform.py playbooks/12-ssh-hardening.yml
```

Of in één loop met fail-on-error:

```bash
for p in 01-bootstrap 02-koha-install 03-koha-apache 04-koha-instance \
         05-koha-config 06-koha-postinstall 07-koha-business 08-koha-finalize \
         09-koha-tls 10-flask-isbn 11-koha-import 12-ssh-hardening; do
  ansible-playbook -i inventory/terraform.py playbooks/${p}.yml || break
done
```

> ℹ️ Alle playbooks zijn idempotent: meerdere keren draaien geeft hetzelfde resultaat. `ON DUPLICATE KEY UPDATE` zorgt dat bestaande data nooit overschreven wordt tenzij gewenst.

---

## 3.4 Selectief draaien per omgeving

Gebruik de `-l` flag om alleen prod of test te targeten:

```bash
# Alleen test
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml -l test

# Alleen prod
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml -l prod
```

De omgeving-specifieke waarden komen uit `inventory/group_vars/prod.yml` resp. `inventory/group_vars/test.yml` (zie doc 05).

---

## 3.5 Vault-decryptie

`ansible.cfg` regel 9 verwijst naar `~/.ansible-vault-pass-koha-saf`. Als dat bestand bestaat hoeft geen extra flag meegegeven worden — vault-decryptie gebeurt automatisch.

Anders expliciet:

```bash
ansible-playbook -i inventory/terraform.py playbooks/10-flask-isbn.yml \
  --vault-password-file ~/.ansible-vault-pass-koha-saf
```

Op dit moment gebruikt alleen `flask_isbn_app` de vault — voor de htpasswd-hash van Basic Auth. Zie doc 24 (security hardening) en `ansible-vault-setup.md`.
