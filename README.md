# README – Koha Project


### koha-saf
Inleiding bibliotheek

## Git
clone eerst de repo op je machine
wijzig voor terraform/terraform.tfvars de ssh keys van je huidige host 
Daarna genereer een key voor de ansible user op je machine 
Verzin een wachtwoord voor je ansible user en hash dat met SHA512
Zet deze in je terraform/terraform.tfvars


## terraform
Installeer terraform op je mac met brew install terraform
Om terraform op te zetten moet je eerst de provider installeren

cd koha-saf/terraform
sudo terraform init

sudo terraform plan \
   -var-file=terraform.tfvars \
   -var-file=secrets/secrets.tfvars

sudo terraform apply \
   -var-file=terraform.tfvars \
   -var-file=secrets/secrets.tfvars



### Selectief droplet verwijderen
Eerst status bebijken
sudo terraform state list

Daarna selecteren en destroyen
sudo terraform destroy \
  -var-file=terraform.tfvars \
  -var-file=secrets/secrets.tfvars \
  -target='digitalocean_droplet.droplet["koha-saf-test"]'


## 1. Doel van dit project

Dit Ansible-project automatiseert de **volledige installatie, configuratie en initiële functionele inrichting van Koha** op een consistente, herhaalbare en beheerbare manier.

Het project is expliciet ontworpen voor:

* **lange-termijn onderhoud**
* **teamgebruik**
* **duidelijke scheiding tussen techniek en bibliotheeklogica**
* **voorbereiding op Vault, security en CI/CD**

Functionele correctheid van Koha wordt als gegeven beschouwd; dit project richt zich op **structuur, beheersbaarheid en transparantie**.

---

## 2. Architectuur-overzicht

### 2.1 Hoofdconcept

De architectuur is **lifecycle-gedreven**:

* *Playbooks* beschrijven **wanneer** iets gebeurt
* *Rollen* beschrijven **wat** er gebeurt
* *Variabelen* beschrijven **hoe** het systeem wordt ingevuld

Er is een expliciete scheiding tussen:

* systeemconfiguratie
* Koha-techniek
* Koha-installatie
* Koha-installer
* Koha business-/bibliotheeklogica

---

### 2.2 Projectstructuur

```text
ansible/
├── ansible.cfg
├── inventory/
│   └── terraform.py
│
├── playbooks/
│   ├── 01-bootstrap.yml
│   ├── 02-koha-install.yml
│   ├── 03-koha-instance.yml
│   ├── 04-koha-config.yml
│   ├── 05-koha-web.yml
│   ├── 06-koha-postinstall.yml
│   └── 07-koha-business.yml
│
├── roles/
│   ├── system_apt/
│   ├── system_swap/
│   ├── koha_repo/
│   ├── koha_install/
│   ├── koha_instance/
│   ├── koha_config/
│   ├── koha_apache/
│   ├── koha_postinstall_python/
│   ├── koha_postinstall_db/
│   ├── koha_postinstall_yaml/
│   ├── koha_business_libraries/
│   ├── koha_business_authorised_values/
│   ├── koha_business_admin/
│   └── koha_business_circulation/
│
├── group_vars/
│   ├── all.yml
│   ├── test.yml
│   └── prod.yml
│
└── host_vars/
    └── (optioneel)
```

---

## 3. Designprincipes

### 3.1 Eén rol = één verantwoordelijkheid

Elke rol heeft een **enkelvoudig doel**, bijvoorbeeld:

* `koha_install`: alleen packages
* `koha_instance`: alleen instance lifecycle
* `koha_business_circulation`: alleen circulation rules

Dit maakt:

* hergebruik mogelijk
* debugging eenvoudiger
* uitbreiding veilig

---

### 3.2 Scheiding techniek vs. business

| Laag      | Voorbeelden                        |
| --------- | ---------------------------------- |
| Technisch | OS, Apache, Koha packages          |
| Installer | SQL-structuur, YAML loaders        |
| Business  | Libraries, admin user, circulation |

Functionele wijzigingen aan de bibliotheekconfiguratie vereisen **geen herinstallatie** van Koha.

---

### 3.3 Variabelenstrategie

* **Defaults**: in roles (veilig, generiek)
* **Configuratie**: in `group_vars`
* **Secrets**: voorlopig plain-text, later Vault

Geen hardcoded waarden in taken.

---

## 4. Lifecycle en uitvoervolgorde

De playbooks moeten **altijd in deze volgorde** worden uitgevoerd:

1. `01-bootstrap.yml`
   OS-basis (APT, swap)

2. `02-koha-install.yml`
   Koha repository en packages

3. `03-koha-instance.yml`
   Koha instance + database

4. `04-koha-config.yml`
   Technische Koha configuratie

5. `05-koha-web.yml`
   Apache configuratie

6. `06-koha-postinstall.yml`
   Koha installer (SQL + YAML)

7. `07-koha-business.yml`
   Bibliotheeklogica (libraries, admin, circulation)

Elke stap bouwt **onvoorwaardelijk voort op de vorige**.

---

## 5. Rollen per fase (samenvatting)

### 5.1 Bootstrap

* `system_apt`
* `system_swap`

### 5.2 Koha installatie

* `koha_repo`
* `koha_install`

### 5.3 Instance

* `koha_instance`

### 5.4 Web

* `koha_apache`

### 5.5 Post-install

* `koha_postinstall_python`
* `koha_postinstall_db`
* `koha_postinstall_yaml`

### 5.6 Business

* `koha_business_libraries`
* `koha_business_authorised_values`
* `koha_business_admin`
* `koha_business_circulation`

---

## 6. Variabelenbeheer

### 6.1 group_vars/all.yml

Bevat **alle Koha-logica** die omgevings-onafhankelijk is:

* Koha instance naam
* Database instellingen
* Libraries
* Admin user
* Authorised values
* Circulation rules
* Paden naar Koha installer data

### 6.2 group_vars/test.yml / prod.yml

Bevat uitsluitend:

* omgevingsspecifieke waarden
* schaalverschillen (swap, resources)
* geen logica

---

## 7. Uitvoering (als ansible user)

### 7.1 Vereisten

* Linux host met:

  * Python 3
  * SSH toegang
* `ansible` user met:

  * sudo-rechten (passwordless aanbevolen)
* Correct inventory (Terraform of statisch)

---

### 7.2 Basiscommando’s

Alle commando’s worden uitgevoerd **als ansible user** vanaf de Ansible control node.

#### Bootstrap

```bash
ansible-playbook playbooks/01-bootstrap.yml
```

#### Koha installatie

```bash
ansible-playbook playbooks/02-koha-install.yml
```

#### Instance aanmaken

```bash
ansible-playbook playbooks/03-koha-instance.yml
```

#### Technische configuratie

```bash
ansible-playbook playbooks/04-koha-config.yml
```

#### Apache configuratie

```bash
ansible-playbook playbooks/05-koha-web.yml
```

#### Koha installer automatiseren

```bash
ansible-playbook playbooks/06-koha-postinstall.yml
```

#### Bibliotheekconfiguratie

```bash
ansible-playbook playbooks/07-koha-business.yml
```

---

### 7.3 Volledige run (clean install)

```bash
ansible-playbook playbooks/01-bootstrap.yml
ansible-playbook playbooks/02-koha-install.yml
ansible-playbook playbooks/03-koha-instance.yml
ansible-playbook playbooks/04-koha-config.yml
ansible-playbook playbooks/05-koha-web.yml
ansible-playbook playbooks/06-koha-postinstall.yml
ansible-playbook playbooks/07-koha-business.yml
```

---

## 8. Wat dit project **niet** doet (bewust)

* Geen secrets management (Vault volgt later)
* Geen security hardening
* Geen CI/CD
* Geen monitoring
* Geen idempotentie-perfectionisme

Dit is **bewust uitgesteld** tot de architectuur stabiel is.

---

## 9. Verwachte vervolgstappen

Zodra dit model stabiel is, zijn logische vervolgstappen:

1. Ansible Vault integratie
2. Secrets scheiden per omgeving
3. Admin permissions en rollen
4. Security hardening
5. CI/CD pipeline
6. Runbook en operationele documentatie

---

## 10. Slot

Dit project is opgezet als **structurele basis**, niet als quick fix.
Het doel is dat elke beheerder, ook zonder Koha-voorkennis, begrijpt:

* wat er gebeurt
* wanneer het gebeurt
* waar aanpassingen thuishoren

Dit document is de referentie voor iedereen die met dit project werkt.
