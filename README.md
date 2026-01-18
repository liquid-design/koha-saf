# README – Koha SAF Project

## 1. Overzicht

Dit repository bevat de **Infrastructure as Code (Terraform)** en **Configuration Management (Ansible)** voor het automatisch uitrollen en configureren van een **Koha ILS-omgeving**.

De huidige README reflecteert de **gerefactorde architectuur** zoals aanwezig in deze repository en vervangt eerdere documentatie.

Doelstellingen:

* herhaalbare en voorspelbare Koha-installaties
* duidelijke lifecycle-fases
* strikte scheiding tussen infrastructuur, techniek en bibliotheeklogica
* geschikt voor teamgebruik en verdere CI/CD-integratie
* CI/CD is bewust nog niet geïmplementeerd; de huidige structuur is hier wel op voorbereid.

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

Terraform vormt de **fundamentele laag** van dit project en is de **single source of truth** voor alles wat met infrastructuur te maken heeft.

Terraform is verantwoordelijk voor:

- provisioning van infrastructuur (bijv. DigitalOcean droplets)
- basis netwerk- en OS-instellingen
- het vastleggen van infrastructuurstatus in state
- het beschikbaar maken van infrastructuurgegevens voor Ansible via outputs

Er worden **geen infrastructuurgegevens hardcoded** in Ansible; alle hostinformatie is afgeleid van Terraform.

---

Helder — je hebt gelijk 👍
Hieronder staat **het volledige Terraform-hoofdstuk (incl. subhoofdstukken 3.1 t/m 3.6)** als **pure Markdown**, **zonder** een omhullende code-block.
Dit kun je **direct copy-pasten in `README.md`** en het rendert correct.

---

## 3. Terraform

Terraform vormt de **fundamentele laag** van dit project en is de **single source of truth** voor alles wat met infrastructuur te maken heeft.

Terraform is verantwoordelijk voor:

* provisioning van infrastructuur (bijv. DigitalOcean droplets)
* basis netwerk- en OS-instellingen
* het vastleggen van infrastructuurstatus in state
* het beschikbaar maken van infrastructuurgegevens voor Ansible via outputs

Er worden **geen infrastructuurgegevens hardcoded** in Ansible; alle hostinformatie is afgeleid van Terraform.

---

### 3.1 Terraform als single source of truth

Alle informatie over servers, IP-adressen, regio’s en omgevingen bestaat **uitsluitend** in Terraform:

* `main.tf` definieert *wat* er bestaat
* `terraform.tfvars` en `secrets.tfvars` bepalen *hoe*
* `terraform.tfstate` beschrijft *wat er daadwerkelijk is uitgerold*

Deze state is leidend voor de rest van het project.

---

### 3.2 Terraform outputs als contract

Terraform exposeert expliciet infrastructuurinformatie via outputs, onder andere:

* droplet naam
* publiek IP-adres
* regio
* tags (bijv. `test`, `prod`)

Deze outputs vormen een **contract** tussen Terraform en Ansible.

Een vereenvoudigd voorbeeld:

```hcl
output "droplets" {
  value = {
    for k, d in digitalocean_droplet.droplet :
    k => {
      name   = d.name
      ip     = d.ipv4_address
      region = d.region
      tags   = d.tags
    }
  }
}
```

Ansible consumeert deze gegevens, maar **definieert ze niet zelf**.

---

### 3.3 Koppeling met Ansible via `terraform.py`

De koppeling tussen Terraform en Ansible gebeurt via een **dynamic inventory script**:

```
ansible/inventory/terraform.py
```

Dit script:

* voert `terraform output -json` uit in de `terraform/` directory
* leest rechtstreeks uit `terraform.tfstate`
* zet Terraform outputs om naar een Ansible inventory
* maakt automatisch groepen aan (`prod`, `test`) op basis van Terraform tags

Hierdoor:

* zijn er **geen statische inventory-bestanden**
* kan infrastructuur niet “vergeten” worden in Ansible
* blijft Terraform leidend over omgevingen

Voorbeeldgebruik:

```bash
ansible-inventory -i inventory/terraform.py --list
ansible-playbook playbooks/07-koha-business.yml -l test
```

---

### 3.4 Terraform workflow

Terraform wordt uitgevoerd vóór Ansible.

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

Na een succesvolle `apply` is de infrastructuur:

* beschikbaar voor Ansible
* automatisch opgenomen in de dynamic inventory

---

### 3.5 Beheer en lifecycle

Selectief verwijderen of aanpassen van resources gebeurt **altijd via Terraform**:

```bash
terraform state list
terraform destroy \
  -var-file=terraform.tfvars \
  -var-file=secrets/secrets.tfvars \
  -target='digitalocean_droplet.droplet["koha-saf-test"]'
```

Ansible mag ervan uitgaan dat:

* hosts bestaan
* IP-adressen correct zijn
* tags kloppen

Als dat niet zo is, is Terraform de plek waar dit wordt opgelost.


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
