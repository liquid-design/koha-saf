# 8. Bekende beperkingen en roadmap

## 8.1 Huidige beperkingen

Beperkingen die op dit moment nog gelden op de productie- en testomgevingen.

| Beperking | Impact | Voorgestelde oplossing |
|-----------|--------|------------------------|
| Geen email/SMTP | Geen herinneringen of bevestigingen, geen `overdue_notices.pl` mail-output | Postfix als sendmail-relay + nieuwe role `koha_business_smtp` (verwijzing naar deze ontbrekende role staat al in `roles/koha_business_sysprefs/defaults/main.yml` regel 79) |
| Geen cron jobs | Geen automatische boetes of database-cleanup | Aparte role `koha_cron` die `overdue_notices.pl`, `fines.pl`, `cleanup_database.pl` als systemd timers deployt |
| Geen UFW / firewall | Alle poorten open op de droplet zelf | DigitalOcean Cloud Firewall via Terraform (poorten 22, 80, 443) — of UFW via een nieuwe role |
| Certbot `bib-le-ssl.conf` op prod | Handmatige `a2dissite` na eerste deploy prod (zie doc 06 §6.4) | Toevoegen aan de disable-loop in `roles/koha_apache-tls-finalize/tasks/main.yml` |
| Default `biblio_framework` ontbreekt | Catalogiseren via webformulieren werkt niet zonder lege "Default" framework | Toevoegen aan `roles/koha_postinstall_db` of nieuwe role `koha_business_frameworks`. Zie `technical debt.md` |

## 8.2 Recent voltooid

Niet meer in scope want al uitgerold:

- **Ansible Vault** — geïntegreerd, `~/.ansible-vault-pass-koha-saf` wordt door `ansible.cfg` regel 9 opgepikt. Actieve vault-vars: `vault_flask_htpasswd_user`, `vault_flask_htpasswd_hash`. Zie `ansible-vault-setup.md` en doc 05 §5.4.
- **Database backup architectuur** — 3-2-1 strategie ontworpen: dagelijkse `koha-dump`/`koha-restore` naar Backblaze B2 (Object Lock, Compliance Mode, 30-dagen retentie), on-premise NAS pull, DigitalOcean weekly snapshots als derde laag. Zie docs 20–23.
- **Zebra silent-failure fix** — `koha_import_runner` start nu Zebra in bootstrap en faalt loud als hij niet draait. Zie `roles/koha_import_runner/tasks/main.yml` regel 50–76.
- **ISBN-scan-app security hardening** — Basic Auth + CSRF + input-validatie + rate limiting. Zie doc 24.

---

## 8.3 Roadmap

### Korte termijn

- [ ] UFW of DigitalOcean Cloud Firewall (poorten 22, 80, 443)
- [ ] `bib-le-ssl.conf` fix in `koha_apache-tls-finalize`
- [ ] `biblio_framework` Default-seed in `koha_postinstall_db` of nieuwe role
- [ ] Implementeren en testen van de `koha_backup` Ansible-role (B2 + retention)

### Middellange termijn

- [ ] Email/SMTP role (`koha_business_smtp` + Postfix)
- [ ] Koha cron-role (`overdue_notices.pl`, `fines.pl`, `cleanup_database.pl` als systemd timers)
- [ ] Koha upgrade-playbook voor minor versies (bv. 25.05 → 25.05.x)
- [ ] Jaarlijkse restore-drill geautomatiseerd (per doc 23)

### Lange termijn

- [ ] Koha REST API integratie voor bulk catalogisering
- [ ] Z39.50 configuratie voor externe catalogusimport (bv. NBD Biblion)
- [ ] SIP2 configuratie voor zelfscan terminals
- [ ] Multi-bibliotheek uitbreiding (extra branches)

---

## 8.4 Open architectuur-keuzes

Punten die nog niet beslist zijn, met de afweging die nog moet gebeuren.

**SMTP via Postfix vs externe service.** Een Postfix-relay op de droplet vergt minimaal extra config maar betekent dat het IP-adres van de droplet in SPF moet, en deliverability is broos op DigitalOcean-IPs. Alternatief: externe SMTP (bv. mail.socialisme.be) via authenticated smarthost. De vault-doc anticipeert al op een `koha_business_smtp` role; concrete keuze nog te maken.

**Firewall op droplet-niveau vs DO Cloud Firewall.** UFW geeft fine-grained per-host control en zit volledig in Ansible. DO Cloud Firewall is provider-managed, zit in Terraform en geldt op netwerk-niveau (verkeer raakt de droplet niet eens). Voor deze use-case is DO Cloud Firewall waarschijnlijk de juistere keuze — minder code in Ansible, en consistent met de "Terraform doet infrastructuur, Ansible doet config" scheiding uit doc 02 §2.1.
