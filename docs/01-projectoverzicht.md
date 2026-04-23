# 1. Projectoverzicht

Dit project automatiseert de volledige installatie en configuratie van Koha — een open-source geïntegreerd bibliotheeksysteem (ILS) — op DigitalOcean cloudinfrastructuur. De volledige stack is beschreven als code: van het provisioneren van servers tot het inrichten van bibliotheeklogica.

Het project is opgebouwd rond drie lagen:

- **Terraform** — provisioning van DigitalOcean Droplets
- **Ansible** — configuratie en applicatie-installatie
- **Koha 25.05** — het bibliotheeksysteem zelf

---

## 1.1 Doelstelling

Een volledig reproduceerbare Koha-omgeving die met één commando per laag uitgerold kan worden, zonder handmatige stappen via de webinterface. De webinstaller wordt volledig omzeild via geautomatiseerde SQL- en YAML-initialisatie.

---

## 1.2 Omgevingen

| Omgeving | Hostname | OPAC URL | Intranet URL |
|----------|----------|----------|--------------|
| Productie | bib.marxisme.be | https://bib.marxisme.be | https://bib-intra.marxisme.be |
| Test | bib-test.marxisme.be | https://bib-test.marxisme.be | https://bib-test-intra.marxisme.be |

---

## 1.3 Accounts

> ⚠️ Deze wachtwoorden zijn hardcoded voor de POC-fase. Vervang ze via Ansible Vault voor productie.

| Username | Naam | Rol | Wachtwoord (POC) |
|----------|------|-----|------------------|
| `kohaadmin` | Karl Marx | Superlibrarian | `Koha1234!` |
| `bibliothecaris` | Rosa Luxemburg | Superlibrarian | `Koha1234!` |
| `catalogisator` | Friedrich Engels | Superlibrarian | `Koha1234!` |
