# 5. Configuratie Referentie

## 5.1 Group vars structuur

Variabelen zijn ingedeeld over vier niveaus:

| Bestand | Variabelen | Encrypted |
|---------|------------|-----------|
| `inventory/group_vars/all/koha.yml` | `koha_repo_baseurl`, `koha_keyring_path`, `koha_version`, `koha_webinstaller_version` | nee |
| `inventory/group_vars/all/system.yml` | `swap_file`, `swap_size`, `swap_swappiness` | nee |
| `inventory/group_vars/all/vault.yml` | `vault_flask_htpasswd_user`, `vault_flask_htpasswd_hash` (zie §5.4) | **ja (Ansible Vault)** |
| `inventory/group_vars/prod.yml` | `koha_instance`, `koha_domain`, `koha_suite`, `koha_opac_domain`, `koha_intranet_domain`, `koha_user`, `letsencrypt_email`, `scan_domain`, SSH-config | nee |
| `inventory/group_vars/test.yml` | Zelfde keys als `prod.yml`, andere waarden voor testomgeving | nee |

> ℹ️ De vault wordt automatisch gedecrypt zolang `~/.ansible-vault-pass-koha-saf` bestaat (gerefereerd in `ansible.cfg` regel 9). Zie verder `ansible-vault-setup.md`.

---

## 5.2 Per-omgeving waarden

Onderstaande tabel toont de actuele inhoud van `prod.yml` en `test.yml`.

| Variabele | Prod | Test |
|-----------|------|------|
| `ansible_user` | `ansible` | `ansible` |
| `ansible_ssh_private_key_file` | `~/.ssh/ansible_nopass` | `~/.ssh/ansible_nopass` |
| `koha_domain` | `.marxisme.be` | `.marxisme.be` |
| `koha_instance` | `bib` | `bib-test` |
| `koha_suite` | `25.05` | `25.05` |
| `koha_opac_domain` | `bib.marxisme.be` | `bib-test.marxisme.be` |
| `koha_intranet_domain` | `bib-intra.marxisme.be` | `bib-test-intra.marxisme.be` |
| `koha_user` | `bib-koha` | `bib-test-koha` |
| `letsencrypt_email` | `sander@liquid-design.be` | `sander@liquid-design.be` |
| `scan_domain` | `scan.marxisme.be` | `scan-test.marxisme.be` |

---

## 5.3 Business defaults aanpassen

Alle bibliotheeklogica staat in `defaults/main.yml` per role. Aanpassen zonder code te wijzigen:

### Nieuwe bibliotheek toevoegen

`roles/koha_business_libraries/defaults/main.yml`:

```yaml
koha_libraries:
  - code: SAF
    name: Steunpunt Antifascisme
  - code: BRU
    name: Brussel filiaal
```

### Item types uitbreiden

`roles/koha_business_item_types/defaults/main.yml` — uncomment DVD of CD:

```yaml
koha_item_types:
  - code: BK
    description: Boek
    loan_period: 14
    renewals: 2
    notforloan: 0

  - code: DVD
    description: DVD
    loan_period: 7
    renewals: 1
    notforloan: 0
```

### Medewerker toevoegen

`roles/koha_business_staff/defaults/main.yml`:

```yaml
koha_staff_users:
  - username: nieuwemedewerker
    cardnumber: "1003"
    firstname: Voornaam
    surname: Achternaam
    category: S
    branch: SAF
    flags: 1
    password_hash: "$2a$08$..."
```

> ℹ️ Genereer een bcrypt-hash met:
> ```bash
> python3 -c "import bcrypt; print(bcrypt.hashpw(b'wachtwoord', bcrypt.gensalt()).decode())"
> ```

### Permissie-flags (bitmask)

| Waarde | Permissie | Beschrijving |
|--------|-----------|--------------|
| `1` | superlibrarian | Volledige toegang |
| `4` | catalogue | Zoeken en raadplegen |
| `2048` | circulate | Uitlenen en terugbrengen |
| `4096` | cataloguing | Boeken invoeren |
| `6144` | circulate + cataloguing | Balie + catalogiseren |

---

## 5.4 Vault-variabelen

`inventory/group_vars/all/vault.yml` wordt versleuteld met Ansible Vault. Op dit moment wordt de vault gebruikt door één role:

| Variabele | Geconsumeerd in | Doel |
|-----------|------------------|------|
| `vault_flask_htpasswd_user` | `roles/flask_isbn_app/defaults/main.yml` regel 28 | Basic Auth gebruikersnaam (op dit moment `saf`) |
| `vault_flask_htpasswd_hash` | `roles/flask_isbn_app/defaults/main.yml` regel 29 | Volledige bcrypt-regel uit `htpasswd -nbB saf '<pw>'` |

Voorbeeld inhoud (na decryptie):

```yaml
vault_flask_htpasswd_user: "saf"
vault_flask_htpasswd_hash: "saf:$2y$05$abcdefghijklmnopqrstuv..."
```

Vault editen:

```bash
ansible-vault edit inventory/group_vars/all/vault.yml
```

> ℹ️ Hash genereer je offline. We gebruiken bewust géén `community.general.htpasswd` Ansible-module — dat zou platte tekst in vars vereisen. Door de hash zelf te schrijven blijft het wachtwoord alleen in de offline `htpasswd -nbB` aanroep. Zie `roles/flask_isbn_app/tasks/main.yml` regel 230–246.

---

## 5.5 Koha systeempreferenties

De belangrijkste sysprefs die door Ansible gezet worden:

| Syspref | Waarde | Effect |
|---------|--------|--------|
| `OPACBaseURL` | `https://{{ koha_opac_domain }}` | Publieke URL van de OPAC |
| `staffClientBaseURL` | `https://{{ koha_intranet_domain }}` | Interne URL van het intranet |
| `language` | `nl` | Interfacetaal intranet |
| `opaclanguages` | `nl` | Interfacetaal OPAC |
| `LibraryName` | `Steunpunt Antifascisme` | Naam in de interface |
| `marcflavour` | `MARC21` | MARC-formaat voor catalogisering |
| `autoBarcode` | `incremental` | Automatische barcode generatie |
| `OverduesBlockCirc` | `ask` | Waarschuwing bij te laat materiaal |
| `OpacPublic` | `1` | Anoniem zoeken toegestaan |
| `opacuserlogin` | `1` | Lezers kunnen inloggen op OPAC |
| `StoreLastBorrower` | `0` | Laatste uitlener niet bewaren (privacy) |

Volledig overzicht in `roles/koha_business_sysprefs/defaults/main.yml`. Aanpassen:

```yaml
koha_sysprefs:
  - pref: LibraryName
    value: "Nieuwe naam"
```

Daarna opnieuw draaien:

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml
```

---

## 5.6 Variabelen die je vermoedelijk nooit hoeft aan te raken

Onderstaande variabelen staan in `group_vars/all/` en wijzigen alleen bij major version-bumps.

```yaml
# inventory/group_vars/all/koha.yml
koha_repo_baseurl: "https://debian.koha-community.org/koha"
koha_keyring_path: /etc/apt/keyrings/koha.asc
koha_version: "25.05"
koha_webinstaller_version: "25.0506000"

# inventory/group_vars/all/system.yml
swap_file: /swapfile
swap_size: 2G
swap_swappiness: 10
```

Bij een Koha-upgrade naar bv. 25.11 hoef je alleen `koha_version`, `koha_webinstaller_version` en `koha_suite` (in beide environment-files) aan te passen.
