# 3. Deploy Pipeline

De volledige installatie bestaat uit twee fasen: infrastructuur (Terraform) en configuratie (Ansible). De Ansible-fase is opgesplitst in 9 genummerde playbooks die in volgorde uitgevoerd worden.

---

## 3.1 Fase 1 — Terraform

### Vereisten

- Terraform ≥ 1.0 geïnstalleerd
- DigitalOcean API token in `secrets/secrets.tfvars`
- SSH keys geconfigureerd in `terraform.tfvars`

### Uitvoering

```bash
cd terraform
terraform init
terraform plan -var-file=secrets/secrets.tfvars
terraform apply -var-file=secrets/secrets.tfvars
```

Terraform maakt aan:

- Twee Droplets (prod + test) met Debian 12
- Cloud-init script: `ansible`-gebruiker, SSH keys, sudo rechten
- DigitalOcean backups en monitoring ingeschakeld

---

## 3.2 Fase 2 — Ansible

Alle playbooks worden uitgevoerd vanuit de `ansible/` map:

```bash
cd ansible
```

| # | Playbook | Verantwoordelijkheid |
|---|----------|----------------------|
| 01 | bootstrap | Locale, swap, system hardening, facts directory |
| 02 | koha-install | Koha APT repository, koha-common, MariaDB |
| 03 | koha-apache | Apache modules, default sites disablen |
| 04 | koha-instance | koha-create, Plack enablen, facts persisteren |
| 05 | koha-config | koha-conf.xml validatie, DB facts laden |
| 06 | koha-postinstall | DB structuur, SQL/YAML initialisatie, MARC21 |
| 07 | koha-business | Libraries, patron cats, item types, staff, sysprefs |
| 08 | koha-finalize | Version syspref, Zebra index rebuild, Plack restart |
| 09 | koha-tls | HTTP vhosts, Certbot, TLS vhosts, site cleanup |

---

## 3.3 Volledige deploy commando's

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
