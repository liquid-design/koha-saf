# 10. Troubleshooting

## 10.1 Veelvoorkomende problemen

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

---

### Certbot faalt: `SSLCertificateFile does not exist`

De TLS vhosts zijn al geladen vóór certbot draaide. De tijdelijke HTTP vhosts zijn overschreven door de definitieve TLS vhosts voordat de certs aanwezig waren.

Reset de situatie:

```bash
sudo a2dissite bib.marxisme.be.conf
sudo a2dissite bib-intra.marxisme.be.conf
sudo systemctl reload apache2
```

Daarna opnieuw draaien:

```bash
ansible-playbook -i inventory/terraform.py playbooks/09-koha-tls.yml
```

---

### Ansible facts ontbreken (`koha runtime facts missing`)

De facts zijn niet gepersisteerd na `koha-create`. Controleer:

```bash
cat /etc/ansible/facts.d/koha.fact
```

Als het bestand ontbreekt, draai playbook 04 opnieuw:

```bash
ansible-playbook -i inventory/terraform.py playbooks/04-koha-instance.yml
```

---

### Koha webinstaller verschijnt na login

De `Version` syspref is niet ingesteld. Koha denkt dat de installatie nog niet voltooid is.

```bash
ansible-playbook -i inventory/terraform.py playbooks/08-koha-finalize.yml
```

---

### Zebra zoekindex leeg — boeken niet vindbaar

Rebuild de index handmatig:

```bash
sudo koha-rebuild-zebra -f -a -b -v bib
```

Voor de testomgeving:

```bash
sudo koha-rebuild-zebra -f -a -b -v bib-test
```

---

### Plack reageert niet

```bash
sudo koha-plack --status bib
sudo koha-plack --restart bib
```

---

### Tab-karakter in YAML playbook (parse error)

Symptoom: `could not find expected ':'` of role wordt overgeslagen.

Controleer op tabs:

```bash
cat -A playbooks/09-koha-tls.yml | grep '\^I'
```

`^I` is een tab-karakter. Vervang door spaties in je editor.

---

## 10.2 Nuttige commando's op de server

| Doel | Commando |
|------|----------|
| Koha logs OPAC | `sudo tail -f /var/log/koha/bib/opac-error.log` |
| Koha logs intranet | `sudo tail -f /var/log/koha/bib/intranet-error.log` |
| Apache config test | `sudo apachectl configtest` |
| Apache actieve sites | `ls -la /etc/apache2/sites-enabled/` |
| Plack status | `sudo koha-plack --status bib` |
| Plack herstart | `sudo koha-plack --restart bib` |
| Zebra herstart | `sudo koha-zebra --restart bib` |
| Zebra index rebuild | `sudo koha-rebuild-zebra -f -a -b -v bib` |
| MariaDB console | `sudo mysql koha_bib` |
| Koha facts bekijken | `cat /etc/ansible/facts.d/koha.fact` |
| Certbot renew test | `sudo certbot renew --dry-run` |
| Let's Encrypt log | `sudo tail -50 /var/log/letsencrypt/letsencrypt.log` |

---

## 10.3 Ansible debug tips

Verhoog verbositeit voor meer output:

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml -vvv
```

Draai alleen specifieke tags:

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml --tags "koha_business_staff"
```

Check-mode (dry run, geen wijzigingen):

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml --check
```
