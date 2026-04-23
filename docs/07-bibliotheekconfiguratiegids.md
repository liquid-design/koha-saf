# 7. Bibliotheekconfiguratiegids

## 7.1 Patron categorieën

| Code | Naam | Type | Inschrijftermijn | Max leeftijd |
|------|------|------|-----------------|--------------|
| `S` | Medewerker | Staff | Geen | 999 |
| `A` | Volwassene | Adult | 365 dagen | 999 |
| `J` | Jeugd | Child | 365 dagen | 17 jaar |

---

## 7.2 Item types

| Code | Beschrijving | Uitleentermijn | Status |
|------|-------------|----------------|--------|
| `BK` | Boek | 14 dagen | Actief |
| `DVD` | DVD | 7 dagen | Uitgecommentarieerd |
| `CD` | CD | 7 dagen | Uitgecommentarieerd |

---

## 7.3 Uitleenregels

| Regel | Waarde | Beschrijving |
|-------|--------|--------------|
| `maxissueqty` | 20 | Maximum aantal gelijktijdige uitleningen |
| `issuelength` | 14 | Standaard uitleentermijn in dagen |
| `renewalsallowed` | 2 | Aantal verlengingen toegestaan |
| `holds_per_day` | 5 | Maximum reserveringen per dag |
| `holds_per_record` | 3 | Maximum reserveringen per exemplaar |
| `onshelfholds` | 1 | Reservering toegestaan als item beschikbaar is |

---

## 7.4 Eerste boek catalogiseren

1. Login op https://bib-intra.marxisme.be met `kohaadmin` / `Koha1234!`
2. Navigeer naar **Catalogisering → Nieuw record**
3. Kies **MARC21 Default Framework**
4. Vul minimaal in:
   - `245` — Titel
   - `100` — Auteur
5. Voeg een item toe: item type `BK`, vestiging `SAF`
6. Barcode wordt automatisch gegenereerd (`autoBarcode: incremental`)

---

## 7.5 Eerste lezer aanmaken

1. Navigeer naar **Lezers → Nieuwe lezer**
2. Kies categorie: `Volwassene (A)` of `Jeugd (J)`
3. Vul naam, adres en e-mail in
4. Sla op — lidnummer wordt automatisch gegenereerd

---

## 7.6 Eerste uitleen

1. Navigeer naar **Uitleen**
2. Scan of typ het lidnummer van de lezer
3. Scan of typ de barcode van het boek
4. Bevestig de uitleen

---

## 7.7 Bibliotheek (branch)

De installatie bevat één vestiging:

| Code | Naam |
|------|------|
| `SAF` | Steunpunt Antifascisme |

Extra vestigingen toevoegen via `ansible/roles/koha_business_libraries/defaults/main.yml` en playbook 07 opnieuw draaien.

---

## 7.8 Authorised values

| Categorie | Waarde | Label |
|-----------|--------|-------|
| `CCODE` | `BOOK` | Boek |

Authorised values worden gebruikt bij het catalogiseren om materiaalsoorten te labelen. Uitbreiden via `ansible/roles/koha_business_authorised_values/defaults/main.yml`.
