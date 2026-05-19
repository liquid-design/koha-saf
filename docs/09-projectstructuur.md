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
    ├── ansible.cfg                      # roles_path, vault_password_file, SSH settings
    ├── inventory/
    │   ├── terraform.py                 # Dynamische inventory op basis van tfstate
    │   └── group_vars/
    │       ├── all/
    │       │   ├── koha.yml             # Gedeelde Koha variabelen
    │       │   ├── system.yml           # Gedeelde systeem variabelen
    │       │   └── vault.yml            # Encrypted (vault_flask_htpasswd_*)
    │       ├── prod.yml                 # Productie-specifieke variabelen
    │       └── test.yml                 # Test-specifieke variabelen
    ├── playbooks/
    │   ├── 01-bootstrap.yml             # OS basis
    │   ├── 02-koha-install.yml          # Koha repo + koha-common
    │   ├── 03-koha-apache.yml           # Apache modules
    │   ├── 04-koha-instance.yml         # koha-create + facts
    │   ├── 05-koha-config.yml           # koha-conf.xml validatie
    │   ├── 06-koha-postinstall.yml      # DB structuur + MARC21
    │   ├── 07-koha-business.yml         # Languages + libraries + sysprefs
    │   ├── 08-koha-finalize.yml         # Version syspref + Zebra rebuild
    │   ├── 09-koha-tls.yml              # HTTP vhosts → certbot → TLS vhosts
    │   ├── 10-flask-isbn.yml            # Scan-app deploy
    │   ├── 11-koha-import.yml           # Import-pipeline + Zebra bootstrap
    │   └── 12-ssh-hardening.yml         # PasswordAuth uit, root key-only
    └── roles/
        ├── locale_fix/                  # → 01
        ├── system_apt/                  # → 01
        ├── system_hardening_users/      # → 01
        ├── system_swap/                 # → 01
        ├── koha_persist_facts/          # → 01 (facts.d dir)
        ├── koha_repo/                   # → 02
        ├── koha_install/                # → 02
        ├── koha_apache/                 # → 03
        ├── koha_instance/               # → 04 (bevat ook facts-persistentie)
        ├── koha_config/                 # → 05
        ├── koha_postinstall_python/     # → 06
        ├── koha_postinstall_db/         # → 06
        ├── koha_postinstall_yaml/       # → 06
        ├── koha_languages/              # → 07 (MOET eerste in playbook)
        ├── koha_business_libraries/     # → 07
        ├── koha_business_patron_categories/ # → 07
        ├── koha_business_item_types/    # → 07
        ├── koha_business_authorised_values/ # → 07
        ├── koha_business_circulation/   # → 07
        ├── koha_business_sysprefs/      # → 07
        ├── koha_business_staff/         # → 07
        ├── koha_business_admin/         # → 07
        ├── koha_finalize/               # → 08
        ├── koha_apache-tls/             # → 09 (fase 1)
        ├── certbot/                     # → 09 (fase 2)
        ├── koha_apache-tls-finalize/    # → 09 (fase 3)
        ├── flask_isbn_app/              # → 10 (heeft files/ + templates/)
        ├── koha_import_runner/          # → 11 (heeft files/ + templates/)
        └── ssh_hardening/               # → 12
```

Totaal: **12 playbooks**, **28 roles**.

---

## 9.2 Role-naamconventies

| Prefix | Domein | Voorbeeld |
|--------|--------|-----------|
| `locale_*` / `system_*` | Besturingssysteem | `system_swap`, `system_apt` |
| `koha_repo` / `koha_install` | Package-niveau Koha-installatie | `koha_install` |
| `koha_apache*` | Webserver-configuratie | `koha_apache-tls-finalize` |
| `koha_instance` / `koha_config` | Instance-aanmaak en technische config | `koha_instance` |
| `koha_postinstall_*` | Database + YAML initialisatie | `koha_postinstall_db` |
| `koha_languages` | Translation files | `koha_languages` |
| `koha_business_*` | Bibliotheeklogica (aanpasbaar zonder code) | `koha_business_staff` |
| `koha_finalize` | Afsluiting Koha-installatie | `koha_finalize` |
| `certbot` | TLS-certificaten | `certbot` |
| `flask_isbn_app` | Scan-app | `flask_isbn_app` |
| `koha_import_runner` | Import-pijplijn | `koha_import_runner` |
| `ssh_hardening` | OS hardening | `ssh_hardening` |

---

## 9.3 Designprincipes

**Scheiding van verantwoordelijkheden** — elke role doet één ding en documenteert expliciet wat buiten scope valt (zie de commentaarblokken bovenaan elke `tasks/main.yml`).

**Idempotentie** — alle database-inserts gebruiken `ON DUPLICATE KEY UPDATE`. Alle file-creates gebruiken `creates:` of `stat`. Playbooks kunnen meerdere keren gedraaid worden zonder bijwerkingen.

**Facts als contract** — de Koha-instance genereert willekeurige credentials. Die worden uitgelezen uit `koha-conf.xml` en opgeslagen als Ansible local facts in `/etc/ansible/facts.d/koha.fact`. Alle volgende roles lezen ze via `ansible_local.koha`. Concreet in `roles/koha_instance/tasks/main.yml` regel 57–113. Dit maakt elke role onafhankelijk uitvoerbaar.

**Defaults als configuratie** — alle bibliotheeklogica staat in `defaults/main.yml`. Operators hoeven geen Ansible-code te begrijpen om de bibliotheek te configureren.

**Fail loud, niet silent** — kritische pre-condities worden expliciet gecontroleerd met `assert` of `failed_when`. Voorbeelden:

| Waar | Wat |
|------|-----|
| `roles/koha_config/tasks/main.yml` regel 10–18 | Assert dat `ansible_local.koha.*` bestaat |
| `roles/koha_import_runner/tasks/main.yml` regel 19–44 | Stat-check op `stage_file.pl` / `commit_file.pl` |
| `roles/koha_import_runner/tasks/main.yml` regel 50–76 | Zebra moet draaien, anders fail loud |
| `roles/ssh_hardening/tasks/main.yml` | `sshd -t` validatie vóór reload |

---

## 9.4 Bestanden buiten de standaard role-structuur

Twee roles hebben naast `defaults/`, `tasks/` en `handlers/` ook `files/` en `templates/`:

```
roles/flask_isbn_app/
├── files/
│   ├── run.py                        # Flask entrypoint
│   ├── requirements.txt              # Python deps
│   └── app/                          # App package (sources, templates, static, ...)
└── templates/
    ├── flask-isbn.service.j2         # Systemd service
    └── scan-vhost.conf.j2            # Apache vhost voor scan-domein

roles/koha_import_runner/
├── files/
│   └── isbn_matcher.sql              # Idempotente seed: ISBN matcher in marc_matchers
└── templates/
    ├── koha-import-runner.path.j2    # Inotify-watch op staging-dir
    ├── koha-import-runner.service.j2 # Wordt door path-unit getriggerd
    └── koha-import-runner.sh.j2      # stage_file.pl + commit_file.pl wrapper
```

`koha_apache-tls-finalize` heeft alleen `templates/`:

```
roles/koha_apache-tls-finalize/templates/
├── koha-opac.conf.j2
└── koha-intranet.conf.j2
```

---

## 9.5 Documentatie-layout

```
koha-docs/
├── 00-from-zero.md                       # Canonieke runbook van kale droplet → werkende stack
├── 01-projectoverzicht.md
├── 02-architectuur.md
├── 03-deploy-pipeline.md                 # 12 playbooks overzicht
├── 04-ansible-roles.md                   # 28 roles in detail
├── 05-configuratie-referentie.md         # Inclusief vault-laag
├── 06-tls-architectuur.md
├── 07-bibliotheekconfiguratiegids.md
├── 08-beperkingen-roadmap.md
├── 09-projectstructuur.md                # ← dit document
├── 10-troubleshooting.md
├── 11-uitleenproces-rollen.md
├── 12-klikpaden-stap-voor-stap.md
├── 13-circulatieregels-matrix.md
├── 14-opac-sysprefs.md
├── 15-testscenario.md
├── 16-visuele-diagrammen.md
├── 20-23-*                               # Backup architectuur + restore runbook
├── 24-ISBN-bronnen ...                   # Dekkingstest
├── 24-security-hardening-scan-app.md     # Scan-app hardening
├── 26-addendum-meertaligheid.md
├── 26-koha-minimale-configuratie.md
├── Nederlandstalige boek-API.md
├── ansible-vault-setup.md
└── technical debt.md
```
