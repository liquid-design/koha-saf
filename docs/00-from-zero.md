# 0. Van zero tot volledige Koha installatie

Dit document is het canonieke runbook voor de volledige deploy: van een kale DigitalOcean droplet (of nog niets) tot een werkende Koha + ISBN-scan + import-pipeline + gehardende SSH. Alles wat hier staat verwijst expliciet naar de playbooks en roles die het werk doen, zodat je weet waar je moet kijken als een stap faalt.

De pijplijn bestaat uit drie fasen:

| Fase | Tool | Resultaat |
|------|------|-----------|
| 0 — Pre-flight | lokale werkstation | SSH-keys, vault-wachtwoord, Terraform variabelen |
| 1 — Provisioning | Terraform | Twee Debian 12 droplets (prod + test) |
| 2 — Configuratie | Ansible (12 playbooks) | Volledig werkende stack |

> ℹ️ Alle Ansible-commando's draaien vanuit `koha-saf/ansible/`. De dynamische inventory `inventory/terraform.py` leest direct uit Terraform state, dus zorg dat fase 1 altijd vóór fase 2 voltooid is.

---

## 0.1 Fase 0 — Pre-flight

Eenmalige setup op je lokale werkstation. Sla dit over als je het al hebt staan.

### 0.1.1 SSH-key voor de `ansible` gebruiker

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/ansible_nopass
```

De public key wordt door Terraform via cloud-init in de `~/.ssh/authorized_keys` van de `ansible`-user gezet. Verwijzing naar het gebruik: `inventory/group_vars/prod.yml` regel 3, `inventory/group_vars/test.yml` regel 3 (`ansible_ssh_private_key_file`).

### 0.1.2 Ansible vault-wachtwoord

```bash
openssl rand -base64 32 > ~/.ansible-vault-pass-koha-saf
chmod 600 ~/.ansible-vault-pass-koha-saf
```

`ansible.cfg` (regel 9) verwacht dit bestand op exact dit pad. Zonder dit bestand falen alle playbooks meteen omdat ze `inventory/group_vars/all/vault.yml` niet kunnen decrypten.

Meer details: zie `ansible-vault-setup.md`.

### 0.1.3 Terraform secrets

```bash
cd terraform
cp secrets/secrets.tfvars.example secrets/secrets.tfvars   # indien aanwezig
$EDITOR secrets/secrets.tfvars
```

Hierin staat de DigitalOcean API-token. Dit bestand staat in `.gitignore` en mag dat blijven.

---

## 0.2 Fase 1 — Terraform

```bash
cd terraform
terraform init
terraform plan  -var-file=secrets/secrets.tfvars
terraform apply -var-file=secrets/secrets.tfvars
```

Terraform maakt aan:

- Twee Droplets in `ams3`, type `s-2vcpu-2gb`, image Debian 12
- Tags `prod` (één droplet) en `test` (de andere) — dit bepaalt later de Ansible-groep, zie `inventory/terraform.py` regel 96–99
- Cloud-init: maakt `ansible`-user aan met passwordless sudo en plaatst de SSH-key
- DigitalOcean backups + monitoring ingeschakeld

Na deze stap kan je controleren of de inventory klopt:

```bash
cd ../ansible
ansible-inventory -i inventory/terraform.py --list
```

Je moet daar twee hosts zien onder de groepen `prod` en `test`.

---

## 0.3 Fase 2 — Ansible: de 12 playbooks in volgorde

Alle commando's vanaf `koha-saf/ansible/`. Je kan elke playbook draaien voor zowel prod als test tegelijk (laat `-l` weg), of selectief met `-l prod` of `-l test`.

### Stap 1 — Bootstrap OS

```bash
ansible-playbook -i inventory/terraform.py playbooks/01-bootstrap.yml
```

**Wat:** Locale, system users, apt cache, swap, facts-directory.
**Playbook:** `playbooks/01-bootstrap.yml`
**Roles:** `locale_fix`, `system_hardening_users`, `system_apt`, `system_swap`, `koha_persist_facts`
**Klaar wanneer:** `/etc/ansible/facts.d/` bestaat, swap is actief (`free -h` toont 2 GB swap).

### Stap 2 — Koha software installeren

```bash
ansible-playbook -i inventory/terraform.py playbooks/02-koha-install.yml
```

**Wat:** Koha apt repository + signing key + `koha-common` package (sleept MariaDB mee).
**Playbook:** `playbooks/02-koha-install.yml`
**Roles:** `koha_repo`, `koha_install`
**Klaar wanneer:** `dpkg -l koha-common` rapporteert versie `25.05.x`.

### Stap 3 — Apache voorbereiden

```bash
ansible-playbook -i inventory/terraform.py playbooks/03-koha-apache.yml
```

**Wat:** Apache-modules `rewrite`, `cgi`, `headers`, `proxy`, `proxy_http` enablen. Default sites uitzetten.
**Playbook:** `playbooks/03-koha-apache.yml`
**Roles:** `koha_apache`
**Klaar wanneer:** `apachectl -M` toont de bovenstaande modules.

### Stap 4 — Koha instance aanmaken

```bash
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
```

**Wat:** `koha-create --create-db <instance>`, Plack enablen + starten, en de gegenereerde DB-credentials persisteren als Ansible facts in `/etc/ansible/facts.d/koha.fact`.
**Playbook:** `playbooks/04-koha-instance.yml`
**Roles:** `koha_instance` (bevat ook de logica van `koha_persist_facts`, zie `roles/koha_instance/tasks/main.yml` vanaf regel 57).
**Klaar wanneer:** `/etc/koha/sites/<instance>/koha-conf.xml` bestaat én `cat /etc/ansible/facts.d/koha.fact` toont een geldig JSON met `db_name`, `db_user`, `db_pass`.

> ⚠️ Vanaf hier zijn de Ansible facts een hard contract. Elke volgende role doet een `assert` op `ansible_local.koha.*` (zie bv. `roles/koha_config/tasks/main.yml` regel 10–18). Als deze stap niet correct afrondt, falen alle latere stappen meteen.

### Stap 5 — Koha technisch configureren

```bash
ansible-playbook -i inventory/terraform.py playbooks/05-koha-config.yml
```

**Wat:** Valideert `koha-conf.xml` en de DB facts.
**Playbook:** `playbooks/05-koha-config.yml`
**Roles:** `koha_config`

### Stap 6 — Webinstaller omzeilen

```bash
ansible-playbook -i inventory/terraform.py playbooks/06-koha-postinstall.yml
```

**Wat:** Wat Koha's webinstaller normaal doet, maar dan via SQL en YAML. Mandatory DB-structuur, MARC21 framework.
**Playbook:** `playbooks/06-koha-postinstall.yml`
**Roles:** `koha_postinstall_python`, `koha_postinstall_db`, `koha_postinstall_yaml`
**Klaar wanneer:** `koha-mysql <instance> -e "SHOW TABLES"` toont een volledig schema (>200 tabellen).

### Stap 7 — Business configuratie

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml
```

**Wat:** Bibliotheekinhoud. Volgorde binnen het playbook is bewust:

1. `koha_languages` — moet **eerst** want het installeert NL/FR vertalingen waarnaar `OPACLanguages` in stap 7 hieronder gaat verwijzen.
2. `koha_business_libraries` — branch SAF
3. `koha_business_patron_categories` — S/A/J
4. `koha_business_item_types` — BK actief
5. `koha_business_authorised_values`
6. `koha_business_circulation` — 14d, 2× verlenging
7. `koha_business_sysprefs` — URLs, taal, MARC21, privacy
8. `koha_business_staff` — Rosa, Friedrich
9. `koha_business_admin` — `kohaadmin`

**Playbook:** `playbooks/07-koha-business.yml`

### Stap 8 — Finaliseren

```bash
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml
```

**Wat:** `Version` syspref zetten (anders verschijnt de webinstaller na login), Zebra index rebuilden, Plack herstarten.
**Playbook:** `playbooks/08-koha-finalize.yml`
**Roles:** `koha_finalize`
**Klaar wanneer:** Je kan inloggen op `https://bib-test.marxisme.be` (na stap 9) en je krijgt het normale Koha-dashboard, niet de webinstaller.

### Stap 9 — TLS uitrollen

```bash
ansible-playbook -i inventory/terraform.py playbooks/09-koha-tls.yml
```

**Wat:** TLS in drie subfasen — de volgorde is essentieel.

1. `koha_apache-tls` deployt tijdelijke HTTP-vhosts (DocumentRoot `/var/www/html`) voor de ACME challenge.
2. `certbot` vraagt cert aan voor OPAC + intranet domein.
3. `koha_apache-tls-finalize` deployt de definitieve TLS-vhosts en disabled de overbodige sites die `koha-create` en `certbot --apache` automatisch aanmaken.

**Playbook:** `playbooks/09-koha-tls.yml`
**Roles:** `koha_apache-tls`, `certbot`, `koha_apache-tls-finalize`
**Klaar wanneer:** `curl -I https://bib-test.marxisme.be` geeft HTTP 200 met een geldig Let's Encrypt cert.

> ⚠️ Bekend issue op prod: `certbot --apache` maakt soms een `bib-le-ssl.conf` aan in plaats van `bib.marxisme.be-le-ssl.conf`. Na de eerste deploy: `sudo a2dissite bib-le-ssl.conf && sudo systemctl reload apache2`. Zie ook doc 06 §6.4.

### Stap 10 — Flask ISBN scan-app

```bash
ansible-playbook -i inventory/terraform.py playbooks/10-flask-isbn.yml
```

**Wat:** Deploy van de Flask-app op `scan.marxisme.be` (prod) of `scan-test.marxisme.be` (test). Draait als `flask-isbn` user achter gunicorn op `127.0.0.1:5000`, met Apache als reverse proxy + Basic Auth. Het cert voor het scan-domein wordt door deze playbook zelf aangevraagd (`certbot certonly --apache`).
**Playbook:** `playbooks/10-flask-isbn.yml`
**Roles:** `flask_isbn_app`
**Vereisten vooraf:**
- Stap 9 moet gedraaid hebben (`certbot` package + Apache TLS-modules)
- De `bib-koha` user moet bestaan (zit in stap 4)
- Vault moet `vault_flask_htpasswd_user` en `vault_flask_htpasswd_hash` bevatten (zie `ansible-vault-setup.md`)

**Klaar wanneer:** `curl -u saf:<pw> https://scan-test.marxisme.be` geeft de ISBN-scan-app terug. De staging-directory `/var/lib/koha-staging/` bestaat met setgid (`drwxrwsr-x`).

### Stap 11 — Import runner

```bash
ansible-playbook -i inventory/terraform.py playbooks/11-koha-import.yml
```

**Wat:** Systemd path-unit (`koha-import-runner.path`) die inotify-watcht op de staging-dir en bij elk nieuw XML-bestand `stage_file.pl` + `commit_file.pl` triggert. Bevat ook de **Zebra bootstrap** die in een vorige iteratie ontbrak.
**Playbook:** `playbooks/11-koha-import.yml`
**Roles:** `koha_import_runner`
**Vereisten vooraf:** Staging-dir bestaat (uit stap 10), `stage_file.pl` en `commit_file.pl` bestaan op het verwachte pad (`/usr/share/koha/bin/`).

Wat deze role specifiek doet en waar (zie `roles/koha_import_runner/tasks/main.yml`):

| Regio | Wat |
|-------|-----|
| ±19–44 | Stat-check op `stage_file.pl` en `commit_file.pl` — faalt loud als ze niet bestaan |
| ±50–76 | Zebra-bootstrap: enable koha-common, start `koha-zebra`, fail loud als hij niet draait |
| ±80–105 | Log-dir en logrotate |
| ±110–145 | ISBN-matcher SQL-seed (idempotent, zonder webinstaller is er anders geen matcher) |
| ±150–170 | Deploy van `koha-import-runner.sh` script |
| ±175–189 | Systemd service + path unit deployen en enablen |

**Klaar wanneer:** `systemctl status koha-import-runner.path` toont `active (waiting)`. Een testbestand in `/var/lib/koha-staging/` moet binnen seconden verdwijnen of in `failed/` belanden.

### Stap 12 — SSH dichttimmeren

```bash
ansible-playbook -i inventory/terraform.py playbooks/12-ssh-hardening.yml
```

**Wat:** PasswordAuthentication uit, root login alleen met key, `MaxAuthTries 4`. Config gaat naar `/etc/ssh/sshd_config.d/99-hardening.conf` (Debian-pattern, upstream config blijft onaangeroerd). De role valideert met `sshd -t` vóór de reload.
**Playbook:** `playbooks/12-ssh-hardening.yml`
**Roles:** `ssh_hardening`

> ⚠️ Bewaar deze playbook expliciet als laatste. Pas wanneer alle voorgaande playbooks succesvol zijn gedraaid is bewezen dat key-based SSH werkt. Als je deze stap eerder draait en je SSH-key zit verkeerd, sluit je jezelf buiten. Pre-flight test:
> ```bash
> ssh -i ~/.ssh/ansible_nopass ansible@<host> 'echo ok'
> ```

---

## 0.4 Volledige eenmalige deploy als één blok

```bash
cd koha-saf/ansible

for p in 01-bootstrap 02-koha-install 03-koha-apache \
         04-koha-instance 05-koha-config 06-koha-postinstall \
         07-koha-business 08-koha-finalize 09-koha-tls \
         10-flask-isbn 11-koha-import 12-ssh-hardening; do
  echo "=== $p ==="
  ansible-playbook -i inventory/terraform.py playbooks/${p}.yml || break
done
```

Alle playbooks zijn idempotent: deze loop kan veilig opnieuw gedraaid worden. Database-inserts gebruiken `ON DUPLICATE KEY UPDATE`, file-creates gebruiken `creates:` of `stat`. Zie ook doc 09 §9.3.

---

## 0.5 Selectief redeployen

Alleen test:

```bash
ansible-playbook -i inventory/terraform.py -l test playbooks/07-koha-business.yml
```

Alleen prod:

```bash
ansible-playbook -i inventory/terraform.py -l prod playbooks/07-koha-business.yml
```

Specifieke role binnen een playbook:

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml \
  --tags "koha_business_staff"
```

> ℹ️ Tags werken alleen als roles ze definiëren. Niet alle roles hebben momenteel tags — bij twijfel draai je gewoon het volledige playbook, het is idempotent.

---

## 0.6 Verifiëren dat alles werkt

| Check | Commando |
|-------|----------|
| Koha OPAC | `curl -sI https://bib-test.marxisme.be \| head -1` |
| Koha staff | `curl -sI https://bib-test-intra.marxisme.be \| head -1` |
| Scan-app | `curl -sI -u saf:<pw> https://scan-test.marxisme.be \| head -1` |
| Zebra draait | `ssh ansible@<host> sudo koha-zebra --status bib-test` |
| Plack draait | `ssh ansible@<host> sudo koha-plack --status bib-test` |
| Import-pad | `ssh ansible@<host> systemctl status koha-import-runner.path` |
| Koha facts | `ssh ansible@<host> sudo cat /etc/ansible/facts.d/koha.fact` |
| SSH gehardend | `ssh -o PreferredAuthentications=password ansible@<host>` → moet falen |

---

## 0.7 Wat dit document niet behandelt

- **Backup architectuur** — zie de docs in de 20-23 reeks (Backblaze B2 + NAS + DO snapshots)
- **Disaster recovery / restore** — zie doc 22 (restore runbook)
- **Catalogiseren en uitlenen vanuit het OPAC/intranet** — zie doc 11 (uitleenproces) en doc 12 (klikpaden)
- **ISBN-bronnen tuning** — zie doc 24 (dekkingstest)
- **Security hardening scan-app** — zie doc 24 (security-hardening)
