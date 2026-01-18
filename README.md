# README – Koha SAF Project

## 1. Overzicht

Dit repository bevat de **Infrastructure as Code (Terraform)** en **Configuration Management (Ansible)** voor het automatisch uitrollen en configureren van een **Koha ILS-omgeving**.

De huidige README reflecteert de **gerefactorde architectuur** zoals aanwezig in deze repository en vervangt eerdere documentatie.

Doelstellingen:

* herhaalbare en voorspelbare Koha-installaties
* duidelijke lifecycle-fases
* strikte scheiding tussen infrastructuur, techniek en bibliotheeklogica
* geschikt voor teamgebruik en verdere CI/CD-integratie

---

## 2. Repository-structuur (high level)

```text
koha-saf/
├── terraform/
│   ├── terraform.tfvars
│   ├── secrets/
│   └── *.tf
│
├── ansible/
│   ├── ansible.cfg
│   ├── inventory/
│   │   └── group_vars/
│   │       └── all/
│   │           └── *.yml
│   │
│   ├── playbooks/
│   │   ├── 01-bootstrap.yml
│   │   ├── 02-koha-install.yml
│   │   ├── 03-koha-apache.yml
│   │   ├── 04-koha-instance.yml
│   │   ├── 05-koha-config.yml
│   │   ├── 06-koha-postinstall.yml
│   │   ├── 07-koha-business.yml
│   │   └── 08-koha-finalize.yml
│   │
│   └── roles/
│       ├── system_apt/
│       ├── system_swap/
│       ├── system_hardening_users/
│       ├── locale_fix/
│       ├── koha_repo/
│       ├── koha_install/
│       ├── koha_apache/
│       ├── koha_instance/
│       ├── koha_config/
│       ├── koha_persist_facts/
│       ├── koha_postinstall_db/
│       ├── koha_postinstall_python/
│       ├── koha_postinstall_yaml/
│       ├── koha_business_libraries/
│       ├── koha_business_authorised_values/
│       ├── koha_business_admin/
│       ├── koha_business_circulation/
│       └── koha_finalize/
│
└── README.md
```

---

## 3. Terraform

Terraform is verantwoordelijk voor:

* provisioning van infrastructuur (bijv. DigitalOcean droplets)
* netwerk- en basis-OS-instellingen

### Stappen

```bash
cd terraform
terraform init
terraform plan \
  -var-file=terraform.tfvars \
  -var-file=secrets/secrets.tfvars
terraform apply \
  -var-file=terraform.tfvars \
  -var-file=secrets/secrets.tfvars
```

Selectief verwijderen van resources:

```bash
terraform state list
terraform destroy \
  -var-file=terraform.tfvars \
  -var-file=secrets/secrets.tfvars \
  -target='digitalocean_droplet.droplet["koha-saf-test"]'
```

---

## 4. Ansible – Architectuur

De Ansible-architectuur is **lifecycle-gedreven**:

* *Playbooks* bepalen de volgorde
* *Rollen* hebben één duidelijke verantwoordelijkheid
* *Variabelen* bepalen de inhoud

### Kernprincipes

* één rol = één taak
* geen businesslogica in technische rollen
* idempotente en herhaalbare runs

---

## 5. Playbook lifecycle

De playbooks moeten **altijd in deze volgorde** worden uitgevoerd:

1. **01-bootstrap.yml**
   Basis OS-configuratie

   * `system_apt`
   * `system_swap`
   * `locale_fix`
   * `system_hardening_users`

2. **02-koha-install.yml**
   Installatie van Koha packages

   * `koha_repo`
   * `koha_install`

3. **03-koha-apache.yml**
   Webserver configuratie

   * `koha_apache`

4. **04-koha-instance.yml**
   Koha instance en database

   * `koha_instance`
   * `koha_persist_facts`

5. **05-koha-config.yml**
   Technische Koha configuratie

   * `koha_config`

6. **06-koha-postinstall.yml**
   Installerfase (initiële vulling)

   * `koha_postinstall_db`
   * `koha_postinstall_python`
   * `koha_postinstall_yaml`

7. **07-koha-business.yml**
   Bibliotheeklogica

   * `koha_business_libraries`
   * `koha_business_authorised_values`
   * `koha_business_admin`
   * `koha_business_circulation`

8. **08-koha-finalize.yml**
   Afronding en validatie

   * `koha_finalize`

---

## 6. Variabelen en configuratie

* **Defaults**: in rollen (`defaults/main.yml`)
* **Omgevingsconfiguratie**: `ansible/inventory/group_vars/all/*.yml`
* **Secrets**: voorlopig plain-text, voorbereid op Vault

Er zijn geen hardcoded waarden in tasks.

---

## 7. Status en toekomst

* structuur is stabiel na refactoring
* voorbereid op:

  * Ansible Vault
  * CI/CD pipelines
  * multi-instance Koha deployments

---

## 8. Onderhoud

Wijzigingen in bibliotheeklogica (circulation, libraries, authorised values) vereisen **geen herinstallatie** van Koha.

Technische wijzigingen blijven beperkt tot hun eigen lifecycle-fase.
