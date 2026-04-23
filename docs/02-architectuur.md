# 2. Architectuur

## 2.1 Infrastructuurlagen

Het project volgt een strikte scheiding van verantwoordelijkheden over drie lagen:

| Laag | Tool | Verantwoordelijkheid |
|------|------|----------------------|
| Infrastructuur | Terraform | Droplets aanmaken, cloud-init, SSH keys, backups, monitoring |
| Configuratie | Ansible | OS hardening, packages, Koha installatie, TLS, business config |
| Applicatie | Koha 25.05 | Bibliotheeksysteem, catalogus, uitleenbeheer, OPAC |

---

## 2.2 Serverspecificaties

| Parameter | Waarde |
|-----------|--------|
| Cloud provider | DigitalOcean |
| Regio | ams3 (Amsterdam) |
| Droplet grootte | s-2vcpu-2gb (2 vCPU, 2 GB RAM) |
| OS | Debian 12 (Bookworm) x64 |
| Swap | 2 GB swapfile (swappiness 10) |
| Backups | Ingeschakeld via DigitalOcean |
| Monitoring | Ingeschakeld via DigitalOcean |

---

## 2.3 Netwerkarchitectuur

Elke Droplet draait Apache als reverse proxy voor Koha's Plack PSGI-server. Inkomend verkeer:

- **Poort 80 (HTTP)** → automatische redirect naar HTTPS via Apache RewriteRule
- **Poort 443 (HTTPS)** → Apache → Plack (UNIX socket) → Koha
- Let's Encrypt TLS-certificaten via Certbot, automatisch vernieuwd

---

## 2.4 Dynamische inventory

Ansible gebruikt geen statische inventory-bestanden. In plaats daarvan leest het Python-script `inventory/terraform.py` de Terraform state uit en genereert dynamisch de inventory. Hierdoor zijn Terraform en Ansible altijd gesynchroniseerd: elk nieuw aangemaakt Droplet is direct beschikbaar voor Ansible.

Omgevingsindeling op basis van DigitalOcean tags:

- Tag `prod` → groep `prod`
- Tag `test` → groep `test`
- Alle hosts → groep `all`

---

## 2.5 Ansible facts persistentie

Koha genereert bij aanmaak willekeurige databasecredentials. Deze worden uitgelezen uit `koha-conf.xml` en opgeslagen in `/etc/ansible/facts.d/koha.fact`. Alle volgende rollen lezen deze facts via `ansible_local.koha` — zonder dat credentials hardcoded hoeven te staan.

```json
{
  "instance": "bib",
  "db_name": "koha_bib",
  "db_user": "koha_bib",
  "db_pass": "<gegenereerd door koha-create>"
}
```
