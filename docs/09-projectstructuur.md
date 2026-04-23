# 9. Projectstructuur

## 9.1 Repository layout

```
koha-saf/
├── terraform/
│   ├── main.tf                          # Provider, resources, outputs
│   ├── terraform.tfvars                 # Droplet configuratie
│   ├── terraform.tfstate                # Gegenereerd door terraform apply
│   └── secrets/
│       └── secrets.tfvars               # DO API token (gitignored)
└── ansible/
    ├── ansible.cfg                      # Roles path, SSH settings
    ├── inventory/
    │   ├── terraform.py                 # Dynamische inventory op basis van tfstate
    │   └── group_vars/
    │       ├── all/
    │       │   ├── koha.yml             # Gedeelde Koha variabelen
    │       │   └── system.yml           # Gedeelde systeemvariabelen
    │       ├── prod.yml                 # Productie-specifieke variabelen
    │       └── test.yml                 # Test-specifieke variabelen
    ├── playbooks/
    │   ├── 01-bootstrap.yml
    │   ├── 02-koha-install.yml
    │   ├── 03-koha-apache.yml
    │   ├── 04-koha-instance.yml
    │   ├── 05-koha-config.yml
    │   ├── 06-koha-postinstall.yml
    │   ├── 07-koha-business.yml
    │   ├── 08-koha-finalize.yml
    │   └── 09-koha-tls.yml
    └── roles/
        ├── locale_fix/
        ├── system_apt/
        ├── system_hardening_users/
        ├── system_swap/
        ├── koha_persist_facts/
        ├── koha_repo/
        ├── koha_install/
        ├── koha_apache/
        ├── koha_apache-tls/
        ├── koha_apache-tls-finalize/
        ├── certbot/
        ├── koha_instance/
        ├── koha_config/
        ├── koha_postinstall_python/
        ├── koha_postinstall_db/
        ├── koha_postinstall_yaml/
        ├── koha_finalize/
        ├── koha_business_libraries/
        ├── koha_business_patron_categories/
        ├── koha_business_item_types/
        ├── koha_business_authorised_values/
        ├── koha_business_circulation/
        ├── koha_business_sysprefs/
        ├── koha_business_staff/
        └── koha_business_admin/
```

---

## 9.2 Role naamconventies

| Prefix | Domein |
|--------|--------|
| `system_` | Besturingssysteem (swap, apt, hardening) |
| `koha_repo` / `koha_install` | Package-niveau installatie |
| `koha_apache*` | Webserver configuratie |
| `koha_instance` / `koha_config` | Instance aanmaak en technische config |
| `koha_postinstall_*` | Database en YAML initialisatie |
| `koha_business_*` | Bibliotheeklogica (aanpasbaar zonder code te wijzigen) |
| `certbot` | TLS certificaat beheer |

---

## 9.3 Designprincipes

**Scheiding van verantwoordelijkheden** — elke role doet één ding en documenteert expliciet wat buiten scope valt (zie commentaarblokken bovenaan elke `tasks/main.yml`).

**Idempotentie** — alle database-inserts gebruiken `ON DUPLICATE KEY UPDATE`. Alle file-creates gebruiken `creates:` of `stat`. Playbooks kunnen meerdere keren gedraaid worden zonder bijwerkingen.

**Facts als contract** — de Koha instance genereert willekeurige credentials. In plaats van deze door te geven via variabelen, worden ze opgeslagen als Ansible local facts en door elke volgende role gelezen via `ansible_local.koha`. Dit maakt elke role onafhankelijk uitvoerbaar.

**Defaults als configuratie** — alle bibliotheeklogica staat in `defaults/main.yml`. Operators hoeven geen Ansible-code te begrijpen om de bibliotheek te configureren.
