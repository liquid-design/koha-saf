# 6. TLS Architectuur

## 6.1 Certbot flow

De TLS-implementatie vereist een specifieke volgorde vanwege de ACME HTTP-01 challenge:

1. `koha_apache-tls` deployt tijdelijke HTTP-only vhosts (`DocumentRoot /var/www/html`)
2. `meta: flush_handlers` forceert een Apache reload zodat de vhosts actief zijn
3. `certbot --apache` voert de ACME challenge uit op poort 80
4. Certbot slaat certificaten op onder `/etc/letsencrypt/live/{{ koha_opac_domain }}/`
5. `koha_apache-tls-finalize` deployt de definitieve TLS vhosts met de correcte cert paden
6. Overbodige sites (aangemaakt door `koha-create` + certbot automatisch) worden gedisabled
7. Apache herlaadt met de definitieve configuratie

---

## 6.2 Certificaat locaties

> ⚠️ Certbot slaat beide domeinen (OPAC + intranet) op onder de map van het eerste `-d` argument. Beide vhosts verwijzen daarom naar `koha_opac_domain` voor de cert paden.

| Omgeving | Cert pad |
|----------|----------|
| Prod | `/etc/letsencrypt/live/bib.marxisme.be/` |
| Test | `/etc/letsencrypt/live/bib-test.marxisme.be/` |

Beide vhosts (OPAC én intranet) gebruiken:

```apache
SSLCertificateFile    /etc/letsencrypt/live/{{ koha_opac_domain }}/fullchain.pem
SSLCertificateKeyFile /etc/letsencrypt/live/{{ koha_opac_domain }}/privkey.pem
```

---

## 6.3 Apache vhost structuur

Na een succesvolle deploy zijn alleen de volgende sites actief:

| Server | Actieve sites |
|--------|---------------|
| `bib.marxisme.be` | `bib.marxisme.be.conf`, `bib-intra.marxisme.be.conf` |
| `bib-test.marxisme.be` | `bib-test.marxisme.be.conf`, `bib-test-intra.marxisme.be.conf` |

Elke `.conf` bevat twee VirtualHost blokken:

```apache
# HTTP → HTTPS redirect
<VirtualHost *:80>
  ServerName bib.marxisme.be
  RewriteEngine On
  RewriteRule ^ https://bib.marxisme.be%{REQUEST_URI} [L,R=301]
</VirtualHost>

# HTTPS met Koha + security headers
<VirtualHost *:443>
  ServerName bib.marxisme.be
  SSLEngine on
  SSLCertificateFile    /etc/letsencrypt/live/bib.marxisme.be/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/bib.marxisme.be/privkey.pem
  ...
  Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains"
  Header always set X-Frame-Options SAMEORIGIN
  Header always set X-Content-Type-Options nosniff
</VirtualHost>
```

---

## 6.4 Overbodige sites disablen

`koha_apache-tls-finalize` disabled automatisch:

```yaml
- "{{ koha_instance }}.conf"           # aangemaakt door koha-create
- "{{ koha_opac_domain }}-le-ssl.conf" # aangemaakt door certbot
- "{{ koha_intranet_domain }}-le-ssl.conf"
```

> ⚠️ Bekend probleem: op de prod server (`bib`) heet de certbot-site `bib-le-ssl.conf` (zonder domeinnaam) in plaats van `bib.marxisme.be-le-ssl.conf`. Dit vereist na de eerste deploy een handmatige stap:
> ```bash
> sudo a2dissite bib-le-ssl.conf
> sudo systemctl reload apache2
> ```
> Dit wordt in een volgende versie van de role opgelost.

---

## 6.5 Certificaat vernieuwing

Certbot installeert automatisch een systemd timer of cron job voor vernieuwing. Testen:

```bash
sudo certbot renew --dry-run
```
