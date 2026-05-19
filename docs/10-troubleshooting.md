# 10. Troubleshooting

Praktische problemen die op de prod- of testomgeving kunnen opduiken, gegroepeerd per laag.

---

## 10.1 Koha-instance problemen

### Apache toont default pagina na TLS deploy

Controleer welke sites actief zijn:

```bash
ls -la /etc/apache2/sites-enabled/
```

Disable overbodige sites:

```bash
sudo a2dissite bib.conf
sudo a2dissite bib-le-ssl.conf
sudo systemctl reload apache2
```

Achtergrond: `koha-create` maakt automatisch `<instance>.conf` aan en `certbot --apache` maakt `*-le-ssl.conf` aan. Beide moeten disabled worden — dat doet `koha_apache-tls-finalize` automatisch (zie `roles/koha_apache-tls-finalize/tasks/main.yml`), behalve voor het bekende `bib-le-ssl.conf` issue (zie doc 06 §6.4).

### Certbot faalt: `SSLCertificateFile does not exist`

De TLS vhosts zijn geladen vóór certbot draaide. Reset:

```bash
sudo a2dissite bib.marxisme.be.conf
sudo a2dissite bib-intra.marxisme.be.conf
sudo systemctl reload apache2
```

Daarna opnieuw:

```bash
ansible-playbook -i inventory/terraform.py playbooks/09-koha-tls.yml
```

### Ansible facts ontbreken: `koha runtime facts missing`

De facts zijn niet gepersisteerd na `koha-create`. Controleer:

```bash
ssh ansible@<host> sudo cat /etc/ansible/facts.d/koha.fact
```

Als het bestand ontbreekt, draai playbook 04 opnieuw — die bevat zowel de instance-aanmaak als de facts-persistentie (`roles/koha_instance/tasks/main.yml` regel 57–113):

```bash
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
```

### Koha-webinstaller verschijnt na login

De `Version` syspref is niet ingesteld. Koha denkt dat de installatie nog niet voltooid is.

```bash
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml
```

### Zebra zoekindex leeg — boeken niet vindbaar

Rebuild manueel:

```bash
sudo koha-rebuild-zebra -f -a -b -v bib       # prod
sudo koha-rebuild-zebra -f -a -b -v bib-test  # test
```

### Plack reageert niet

```bash
sudo koha-plack --status bib
sudo koha-plack --restart bib
```

---

## 10.2 Scan-app problemen (playbook 10)

### Scan-app vraagt geen wachtwoord

Apache Basic Auth is niet correct geladen. Controleer:

```bash
ssh ansible@<host> 'sudo apachectl -M | grep -E "auth_basic|authn_file|authz_user"'
```

Alle drie moeten present zijn. Zo niet, draai playbook 10 opnieuw — de role enabled ze (`roles/flask_isbn_app/tasks/main.yml` regel 215–224).

### Scan-app start niet

```bash
ssh ansible@<host> 'systemctl status flask-isbn'
ssh ansible@<host> 'sudo journalctl -u flask-isbn -n 50'
```

Veelvoorkomende oorzaken:

- Venv ontbreekt of incompleet → `sudo rm -rf /opt/isbn_lookup/.venv` en playbook 10 opnieuw
- `.flask_secret` ontbreekt → playbook 10 opnieuw (regenereert eenmalig, idempotent)
- Permissies op `/opt/isbn_lookup` fout → playbook 10 opnieuw

### Vault decryptie faalt

```
ERROR! Attempting to decrypt but no vault secrets found
```

`~/.ansible-vault-pass-koha-saf` ontbreekt of heeft verkeerde rechten. Zie `ansible-vault-setup.md`.

---

## 10.3 Import-pipeline problemen (playbook 11)

### Bestand verschijnt in staging maar wordt niet geïmporteerd

Check de path-unit:

```bash
ssh ansible@<host> 'systemctl status koha-import-runner.path'
ssh ansible@<host> 'systemctl list-timers --all | grep koha'
```

Status moet `active (waiting)` zijn. Niet? Restart:

```bash
ssh ansible@<host> 'sudo systemctl restart koha-import-runner.path'
```

### Bestand belandt in `failed/` maar zou moeten werken

Check de log:

```bash
ssh ansible@<host> 'sudo tail -100 /var/log/koha-import/import.log'
```

### Duplicates worden niet gedetecteerd

Dit was het Zebra-silent-failure issue. De nieuwe `koha_import_runner` faalt loud als Zebra niet draait, maar voor de zekerheid:

```bash
ssh ansible@<host> 'sudo koha-zebra --status bib'
# Moet "running for ..." tonen
```

Niet running? Start hem:

```bash
ssh ansible@<host> 'sudo koha-zebra --start bib'
ssh ansible@<host> 'sudo systemctl enable koha-common.service'
```

Of draai playbook 11 opnieuw — de bootstrap-sectie regelt dit (`roles/koha_import_runner/tasks/main.yml` regel 50–76).

### ISBN matcher ontbreekt

Symptoom: `stage_file.pl --match 1` geeft errors. Check:

```bash
ssh ansible@<host> 'sudo koha-mysql bib -BN -e \
  "SELECT matcher_id, code FROM marc_matchers;"'
```

Geen rij met `ISBN`? Draai playbook 11 opnieuw — de matcher-seed-task is idempotent (zie `roles/koha_import_runner/tasks/main.yml` regel 125–155).

---

## 10.4 SSH problemen (playbook 12)

### Lockout na hardening

Als je per ongeluk playbook 12 draaide zonder werkende key-based SSH: gebruik de DigitalOcean web-console om in te loggen als root, dan:

```bash
sudo rm /etc/ssh/sshd_config.d/99-hardening.conf
sudo systemctl reload ssh
```

Stel je SSH-key correct in, draai dan playbook 12 opnieuw.

### Sshd reload faalt

De role valideert met `sshd -t` vóór reload (`roles/ssh_hardening/tasks/main.yml`). Als die check faalt zie je een duidelijke error in de Ansible-output — de config wordt dan **niet** geactiveerd, dus je SSH-toegang blijft werken.

---

## 10.5 Nuttige commando's op de server

| Doel | Commando |
|------|----------|
| Koha logs OPAC | `sudo tail -f /var/log/koha/bib/opac-error.log` |
| Koha logs intranet | `sudo tail -f /var/log/koha/bib/intranet-error.log` |
| Apache config test | `sudo apachectl configtest` |
| Apache actieve sites | `ls -la /etc/apache2/sites-enabled/` |
| Plack status | `sudo koha-plack --status bib` |
| Plack herstart | `sudo koha-plack --restart bib` |
| Zebra status | `sudo koha-zebra --status bib` |
| Zebra index rebuild | `sudo koha-rebuild-zebra -f -a -b -v bib` |
| MariaDB console | `sudo koha-mysql bib` |
| Koha facts bekijken | `sudo cat /etc/ansible/facts.d/koha.fact` |
| Scan-app status | `sudo systemctl status flask-isbn` |
| Scan-app logs | `sudo journalctl -u flask-isbn -f` |
| Import-pipeline status | `sudo systemctl status koha-import-runner.path` |
| Import-pipeline logs | `sudo tail -f /var/log/koha-import/import.log` |
| Failed imports | `ls -la /var/lib/koha-staging/failed/` |
| Certbot renew test | `sudo certbot renew --dry-run` |
| Let's Encrypt log | `sudo tail -50 /var/log/letsencrypt/letsencrypt.log` |
| SSH hardening config | `sudo cat /etc/ssh/sshd_config.d/99-hardening.conf` |

---

## 10.6 Ansible debug-tips

Verhoog verbositeit voor meer output:

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml -vvv
```

Check-mode (dry run, geen wijzigingen):

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml --check
```

Inventory-output controleren (gaat het naar de juiste hosts?):

```bash
ansible-inventory -i inventory/terraform.py --list
ansible -i inventory/terraform.py test -m ping
```

Een single role binnen een playbook draaien (alleen werkt als die role tags definieert):

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml \
  --tags "koha_business_staff"
```

---

## 10.7 Tab-karakter in YAML playbook (parse error)

Symptoom: `could not find expected ':'` of een role wordt overgeslagen.

Controleer op tabs:

```bash
cat -A playbooks/01-bootstrap.yml | grep '\^I'
```

`^I` is een tab-karakter. Vervang door spaties in je editor.

> ℹ️ In `playbooks/01-bootstrap.yml` regel ±35 (vóór de `koha_persist_facts` regel) staat momenteel een echte tab; idempotent gefixt wordt dit het beste door je editor op "spaces only" te zetten in dit project.
