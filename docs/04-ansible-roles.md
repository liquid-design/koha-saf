# 4. Ansible Roles

## 4.1 Systeemroles

| Role | Verantwoordelijkheid |
|------|----------------------|
| `locale_fix` | Genereert `en_US.UTF-8` locale; vermijdt Perl/Koha encoding warnings |
| `system_hardening_users` | Password ageing, root wachtwoord instellen |
| `system_apt` | APT cache, base packages (curl, gnupg, ca-certificates) |
| `system_swap` | 2 GB swapfile aanmaken, activeren, persisteren in fstab |
| `koha_persist_facts` | Maakt `/etc/ansible/facts.d/` aan |

---

## 4.2 Koha installatie roles

| Role | Verantwoordelijkheid |
|------|----------------------|
| `koha_repo` | Officiële Koha APT repository + GPG signing key |
| `koha_install` | `koha-common` + MariaDB packages, `DOMAIN` instellen |
| `koha_apache` | Apache modules enablen, default sites disablen |
| `koha_instance` | `koha-create`, Plack enablen, DB facts uit `koha-conf.xml` lezen en persisteren |
| `koha_config` | DB facts valideren en beschikbaar stellen |
| `koha_postinstall_python` | Python3 + `python3-pymysql` installeren |
| `koha_postinstall_db` | DB structuur + mandatory SQL bestanden importeren |
| `koha_postinstall_yaml` | Mandatory YAML + MARC21 framework laden via `koha-shell` |
| `koha_finalize` | Version syspref, Zebra rebuild, Zebra + Plack restart |

---

## 4.3 TLS roles

| Role | Verantwoordelijkheid |
|------|----------------------|
| `koha_apache-tls` | **FASE 1:** SSL/rewrite/headers modules, tijdelijke HTTP vhosts deployen, `flush_handlers` |
| `certbot` | Certbot installeren, certificaten aanvragen via `--apache` plugin |
| `koha_apache-tls-finalize` | **FASE 2:** definitieve TLS vhosts, overbodige sites disablen, Apache reload |

> ℹ️ De TLS-volgorde is kritiek: HTTP vhosts moeten bestaan vóór Certbot de ACME HTTP-01 challenge uitvoert. `koha_apache-tls-finalize` draait altijd ná `certbot`.

---

## 4.4 Business configuration roles

| Role | Defaults bestand | Verantwoordelijkheid |
|------|-----------------|----------------------|
| `koha_business_libraries` | `defaults/main.yml` | Branches (SAF: Steunpunt Antifascisme) |
| `koha_business_patron_categories` | `defaults/main.yml` | Lezerscategorieën S/A/J |
| `koha_business_item_types` | `defaults/main.yml` | Item types (BK actief, DVD/CD in commentaar) |
| `koha_business_authorised_values` | `defaults/main.yml` | CCODE: BOOK = Boek |
| `koha_business_circulation` | `defaults/main.yml` | Uitleenregels (14 dagen, 2 verlengingen) |
| `koha_business_sysprefs` | `defaults/main.yml` | URLs, taal, MARC21, privacy |
| `koha_business_staff` | `defaults/main.yml` | Medewerkers met bcrypt wachtwoord + permissies |
| `koha_business_admin` | `defaults/main.yml` | `kohaadmin` superlibrarian |

---

## 4.5 Role structuur

Elke role volgt de standaard Ansible structuur:

```
roles/koha_business_example/
├── defaults/
│   └── main.yml    # Aanpasbare variabelen (libraries, users, regels...)
├── tasks/
│   └── main.yml    # Ansible tasks
└── handlers/
    └── main.yml    # Handlers (bijv. reload apache) — waar van toepassing
```

Business roles hebben geen `templates/` of `vars/` — alle configuratie zit in `defaults/main.yml` zodat aanpassingen geen codewijzigingen vereisen.
