# 4. Ansible Roles

Het project telt **28 roles**, verdeeld over zeven domeinen. Dit document beschrijft elke role: verantwoordelijkheid, gebruikte variabelen, en welk playbook hem aanroept. Alle paden zijn relatief aan `koha-saf/ansible/`.

---

## 4.1 Systeem-roles

Gebruikt door playbook `01-bootstrap.yml`.

| Role | Verantwoordelijkheid | Defaults uit |
|------|----------------------|--------------|
| `locale_fix` | Genereert `en_US.UTF-8`; voorkomt Perl/Koha encoding warnings | (geen vars) |
| `system_hardening_users` | Password ageing in `/etc/login.defs`, root wachtwoord zetten | (geen vars) |
| `system_apt` | APT cache update + base packages (curl, gnupg, ca-certificates, lsb-release) | (geen vars) |
| `system_swap` | 2 GB swapfile aanmaken, activeren, persisteren in fstab | `group_vars/all/system.yml` (`swap_file`, `swap_size`, `swap_swappiness`) |
| `koha_persist_facts` | Maakt `/etc/ansible/facts.d/` aan zodat latere roles facts kunnen schrijven | (geen vars) |

---

## 4.2 Koha installatie-roles

| Role | Aangeroepen door | Verantwoordelijkheid |
|------|------------------|----------------------|
| `koha_repo` | `02-koha-install.yml` | Officiële Koha APT repository + GPG signing key (uit `koha_repo_baseurl`) |
| `koha_install` | `02-koha-install.yml` | `koha-common` (sleept MariaDB mee) — non-interactive |
| `koha_apache` | `03-koha-apache.yml` | Apache modules `rewrite`, `cgi`, `headers`, `proxy`, `proxy_http`; default sites disablen |
| `koha_instance` | `04-koha-instance.yml` | `koha-create --create-db`, Plack enablen + starten. Bevat ook de facts-persistentie (zie §4.2.1) |
| `koha_config` | `05-koha-config.yml` | Validatie van `koha-conf.xml` en DB facts |
| `koha_postinstall_python` | `06-koha-postinstall.yml` | Python3 + `python3-pymysql` |
| `koha_postinstall_db` | `06-koha-postinstall.yml` | Mandatory SQL structuur uit Koha-broncode importeren |
| `koha_postinstall_yaml` | `06-koha-postinstall.yml` | Mandatory YAML + MARC21 framework via `koha-shell` + `load_yaml.pl` |
| `koha_finalize` | `08-koha-finalize.yml` | `Version` syspref zetten, Zebra rebuild, Plack restart |

### 4.2.1 Bijzonderheid: `koha_instance` bevat ook `koha_persist_facts`

Historisch is `koha_persist_facts` apart benoemd, maar de actuele logica zit in `roles/koha_instance/tasks/main.yml` vanaf regel 57. Wat daar gebeurt:

1. `stat` of `/etc/ansible/facts.d/koha.fact` al bestaat (idempotentie).
2. `xmlstarlet` leest `db_name`, `db_user`, `db_pass` uit `koha-conf.xml`.
3. Resultaat wordt weggeschreven als JSON-fact:

```json
{
  "instance": "bib-test",
  "db_name":  "koha_bib-test",
  "db_user":  "koha_bib-test",
  "db_pass":  "<willekeurig gegenereerd door koha-create>"
}
```

Alle volgende roles lezen dit via `ansible_local.koha.*`. Zie doc 02 §2.5.

---

## 4.3 TLS-roles

Gebruikt door playbook `09-koha-tls.yml`. Volgorde binnen het playbook is kritiek.

| Role | Verantwoordelijkheid |
|------|----------------------|
| `koha_apache-tls` | **Fase 1:** SSL/rewrite/headers modules, tijdelijke HTTP vhosts (DocumentRoot `/var/www/html`), `meta: flush_handlers` zodat ze meteen actief zijn |
| `certbot` | Certbot installeren, certificaten aanvragen via `certbot --apache` (poort 80 ACME HTTP-01 challenge) |
| `koha_apache-tls-finalize` | **Fase 2:** definitieve TLS vhosts uit Jinja2 templates, overbodige sites disablen (`<instance>.conf`, `*-le-ssl.conf`), Apache reload |

> ℹ️ De TLS-volgorde is kritiek: HTTP vhosts moeten bestaan vóór Certbot de ACME HTTP-01 challenge uitvoert. `koha_apache-tls-finalize` draait altijd ná `certbot`. Zie ook doc 06.

---

## 4.4 Business-roles (Koha-inhoud)

Allemaal aangeroepen door playbook `07-koha-business.yml`. De volgorde in dat playbook is bewust:

1. **`koha_languages`** moet **eerst** — zonder geïnstalleerde translation files faalt `OPACLanguages` later met onbruikbare waarden.
2. Daarna komen de andere business-roles.

| Role | Defaults bestand | Verantwoordelijkheid |
|------|-----------------|----------------------|
| `koha_languages` | `defaults/main.yml` | `koha-translate` installatie van `nl-NL`, `fr-FR` (Engels is brontaal) |
| `koha_business_libraries` | `defaults/main.yml` | Branches (SAF: Steunpunt Antifascisme) |
| `koha_business_patron_categories` | `defaults/main.yml` | Lezerscategorieën S (Medewerker) / A (Volwassene) / J (Jeugd) |
| `koha_business_item_types` | `defaults/main.yml` | Item types (BK actief; DVD/CD in commentaar) |
| `koha_business_authorised_values` | `defaults/main.yml` | CCODE waarden |
| `koha_business_circulation` | `defaults/main.yml` | Uitleenregels (14 dagen, 2 verlengingen) |
| `koha_business_sysprefs` | `defaults/main.yml` | URLs, taal, MARC21, privacy |
| `koha_business_staff` | `defaults/main.yml` | Medewerkers met bcrypt wachtwoord + permissie-flags |
| `koha_business_admin` | `defaults/main.yml` | `kohaadmin` superlibrarian |

---

## 4.5 Applicatie-roles (scan-app + import-pipeline)

Buiten Koha zelf draait er een ISBN-scan-app en een import-pijplijn die XML-bestanden automatisch in Koha importeert.

### 4.5.1 `flask_isbn_app`

**Aangeroepen door:** `10-flask-isbn.yml`
**Defaults:** `roles/flask_isbn_app/defaults/main.yml`
**Vault-vars:** `vault_flask_htpasswd_user`, `vault_flask_htpasswd_hash`
**Files:** `roles/flask_isbn_app/files/{run.py, requirements.txt, app/}`
**Templates:** `roles/flask_isbn_app/templates/{flask-isbn.service.j2, scan-vhost.conf.j2}`

Wat de role doet, in volgorde (zie `tasks/main.yml`):

| Sectie | Wat |
|--------|-----|
| 1. System packages | python3, venv, pip, passlib, apache2-utils |
| 2. Users en groups | `flask-isbn` user, shared group `koha-import`, `bib-koha` toevoegen aan die group |
| 3. Directories | App-dir `/opt/isbn_lookup`, staging-dir `/var/lib/koha-staging` met **setgid bit** (mode 2775) zodat nieuwe files de juiste group erven |
| 4. App-bestanden | Deploy van `run.py`, `requirements.txt`, hele `app/` package via `copy:` |
| 5. Python venv | Venv in `/opt/isbn_lookup/.venv`, pip upgrade, requirements, gunicorn |
| 6. Systemd | Secret key genereren (eenmalig), `flask-isbn.service` deployen, enablen + starten |
| 7. Apache reverse proxy | Modules (auth_basic, authn_file, authz_user), htpasswd uit vault, certbot voor `scan.<domain>`, vhost deployen |

### 4.5.2 `koha_import_runner`

**Aangeroepen door:** `11-koha-import.yml`
**Defaults:** `roles/koha_import_runner/defaults/main.yml`
**Files:** `roles/koha_import_runner/files/isbn_matcher.sql`
**Templates:** `roles/koha_import_runner/templates/{koha-import-runner.path.j2, koha-import-runner.service.j2, koha-import-runner.sh.j2}`

| Sectie (in `tasks/main.yml`) | Wat |
|------------------------------|-----|
| 1. Verifieer Koha-tools (±19–44) | `stat` op `stage_file.pl` en `commit_file.pl` — fail loud bij ontbreken |
| 2. Zebra bootstrap (±50–76) | `koha-common` enable, `koha-zebra --start <instance>`, **fail loud** als Zebra niet running is (anders glipt elke duplicate ISBN door zonder match) |
| 3. Log directory (±80–105) | `/var/log/koha-import` + logrotate, 30 dagen retention |
| 4. Failed-dir (±110–120) | `/var/lib/koha-staging/failed/` voor afgewezen bestanden |
| 5. ISBN matcher seed (±125–155) | `isbn_matcher.sql` deployen + idempotent toepassen, matcher_id ophalen — zonder webinstaller bestaat er geen matcher en faalt duplicate-detectie |
| 6. Import script (±160–172) | Template `koha-import-runner.sh.j2` deployen naar `/usr/local/sbin/koha-import-runner.sh` |
| 7. Systemd units (±175–189) | `koha-import-runner.service` + `koha-import-runner.path` deployen, daemon-reload, path-unit enablen |

> ℹ️ De **service-unit** wordt niet enabled — alleen de **path-unit**. Systemd triggert de service automatisch wanneer er een bestand verschijnt in de gewatchte directory.

---

## 4.6 SSH-hardening role

| Role | Aangeroepen door | Verantwoordelijkheid |
|------|------------------|----------------------|
| `ssh_hardening` | `12-ssh-hardening.yml` | `/etc/ssh/sshd_config.d/99-hardening.conf` met `PasswordAuthentication no`, `PermitRootLogin prohibit-password`, `MaxAuthTries 4`. Validatie met `sshd -t` vóór reload. |

Volgt het Debian-pattern: upstream `/etc/ssh/sshd_config` blijft onaangeroerd, hardening zit in een drop-in onder `sshd_config.d/`.

---

## 4.7 Role-structuur

Elke role volgt de standaard Ansible-structuur:

```
roles/<role_name>/
├── defaults/
│   └── main.yml      # Aanpasbare variabelen
├── tasks/
│   └── main.yml      # Ansible tasks
├── handlers/
│   └── main.yml      # Handlers (bv. reload apache) — waar van toepassing
├── files/            # Statische bestanden — alleen flask_isbn_app, koha_import_runner
└── templates/        # Jinja2 templates — apache-tls-finalize, flask_isbn_app, koha_import_runner
```

Business-roles hebben enkel `defaults/` + `tasks/` — alle configuratie zit in `defaults/main.yml` zodat aanpassingen geen codewijzigingen vereisen.

---

## 4.8 Open punt — biblio_framework seed

In `technical debt.md` staat één openstaande seed die nog in een role moet:

```sql
INSERT INTO biblio_framework (frameworkcode, frameworktext) VALUES ("", "Default");
```

Tot dit in een role zit moet je dit na stap 06 handmatig draaien:

```bash
ssh ansible@<host> 'sudo koha-mysql <instance> -e \
  "INSERT INTO biblio_framework (frameworkcode, frameworktext) VALUES (\"\", \"Default\");"'
```

Logische plaats om dit op te lossen: een aparte task in `koha_postinstall_db` of een nieuwe role `koha_business_frameworks`.
