# 8. Bekende Beperkingen en Roadmap

## 8.1 Huidige beperkingen (POC)

| Beperking | Impact | Oplossing |
|-----------|--------|-----------|
| Wachtwoorden hardcoded | Security risico bij gedeelde repo | Ansible Vault integratie (Vault is al uitgerold) |
| Geen email/SMTP | Geen herinneringen of bevestigingen | Postfix + Koha messaging config |
| Geen cron jobs | Geen automatische boetes of opruiming | Koha cron configuratie in apart playbook |
| Geen firewall | Alle poorten open | UFW of DigitalOcean Cloud Firewall |
| Certbot `bib-le-ssl.conf` | Handmatige `a2dissite` na eerste deploy prod | Toevoegen aan `koha_apache-tls-finalize` loop |
| Geen database backup | Dataverlies bij servercrash | Automated MariaDB dumps + DigitalOcean Spaces |

---

## 8.2 Roadmap

### Korte termijn

- [ ] Ansible Vault voor wachtwoorden en API tokens
- [ ] UFW firewall configuratie (poort 22, 80, 443 only)
- [ ] `bib-le-ssl.conf` fix in `koha_apache-tls-finalize`

### Middellange termijn

- [ ] Email/SMTP configuratie (Postfix + Koha messaging)
- [ ] Automatische Koha cron jobs (`overdue_notices.pl`, `fines.pl`, `cleanup_database.pl`)
- [ ] MariaDB backup playbook naar DigitalOcean Spaces
- [ ] Koha upgrade playbook (minor versies)

### Lange termijn

- [ ] Koha REST API integratie voor bulk catalogisering
- [ ] Z39.50 configuratie voor externe catalogusimport (bv. NBD Biblion)
- [ ] SIP2 configuratie voor zelfscan terminals
- [ ] Multi-bibliotheek uitbreiding (extra branches)

---

## 8.3 Ansible Vault integratie (volgende stap)

De Vault server is al uitgerold als onderdeel van de homelab stack. Integratie:

1. Maak een Vault-gebaseerd Ansible lookup voor wachtwoorden
2. Vervang hardcoded `password_hash` waarden in `koha_business_staff/defaults/main.yml`
3. Vervang de DigitalOcean API token in `secrets/secrets.tfvars`

```yaml
# Voorbeeld toekomstige integratie
password_hash: "{{ lookup('hashi_vault', 'secret=koha/staff/bibliothecaris:password_hash') }}"
```
