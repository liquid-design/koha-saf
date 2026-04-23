# 5. Configuratie Referentie

## 5.1 Group vars structuur

Variabelen zijn ingedeeld in drie niveaus:

| Bestand | Variabelen |
|---------|------------|
| `group_vars/all/koha.yml` | `koha_repo_baseurl`, `koha_version`, `koha_webinstaller_version` |
| `group_vars/all/system.yml` | `swap_file`, `swap_size`, `swap_swappiness` |
| `group_vars/prod.yml` | `koha_instance`, `koha_opac_domain`, `koha_intranet_domain`, `koha_user`, `letsencrypt_email` |
| `group_vars/test.yml` | Zelfde variabelen, andere waarden voor testomgeving |

---

## 5.2 Business defaults aanpassen

Alle bibliotheeklogica staat in `defaults/main.yml` per role. Aanpassen zonder code te wijzigen:

### Nieuwe bibliotheek toevoegen

`ansible/roles/koha_business_libraries/defaults/main.yml`:

```yaml
koha_libraries:
  - code: SAF
    name: Steunpunt Antifascisme
  - code: BRU
    name: Brussel filiaal
```

### Item types uitbreiden

`ansible/roles/koha_business_item_types/defaults/main.yml` — verwijder commentaar bij DVD of CD:

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

`ansible/roles/koha_business_staff/defaults/main.yml`:

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

> ℹ️ Genereer een bcrypt hash met:
> ```bash
> python3 -c "import bcrypt; print(bcrypt.hashpw(b'wachtwoord', bcrypt.gensalt()).decode())"
> ```

### Permissie flags (bitmask)

| Waarde | Permissie | Beschrijving |
|--------|-----------|--------------|
| `1` | superlibrarian | Volledige toegang |
| `4` | catalogue | Zoeken en raadplegen |
| `2048` | circulate | Uitlenen en terugbrengen |
| `4096` | cataloguing | Boeken invoeren |
| `6144` | circulate + cataloguing | Balie + catalogiseren |

---

## 5.3 Koha systeempreferenties

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

Sysprefs aanpassen in `ansible/roles/koha_business_sysprefs/defaults/main.yml`:

```yaml
koha_sysprefs:
  - pref: LibraryName
    value: "Nieuwe naam"
```

Na aanpassing opnieuw draaien:

```bash
ansible-playbook -i inventory/terraform.py playbooks/07-koha-business.yml
```
