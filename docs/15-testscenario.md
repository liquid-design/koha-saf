# 15. Testscenario — proefuitleen met 3 personen en 5 boeken

Dit document is een afvinkbaar testscenario waarmee je in 60-90 minuten kunt valideren dat het volledige uitleenproces in Koha 25.05 werkt zoals verwacht.

**Voorwaarde:** Koha is geïnstalleerd, branches/categorieën/itemtypes zijn geconfigureerd ([doc 7](./07-bibliotheekconfiguratiegids.md)), circulatieregels staan ([doc 13](./13-circulatieregels-matrix.md)), OPAC sysprefs zijn ingesteld ([doc 14](./14-opac-sysprefs.md)).

> **Aanbeveling:** doe deze test in de **test-omgeving** (`bib-test.marxisme.be` / `bib-test-intra.marxisme.be`), niet in productie.

---

## 15.1 De testopstelling

### Drie testers (rollen)

| Tester | Naam in dit scenario | Rol     | Login                             |
| ------ | -------------------- | ------- | --------------------------------- |
| 1      | Alex Admin           | Admin   | `kohaadmin` (al aangemaakt)       |
| 2      | Sam Staff            | Staff   | aanmaken in stap 15.2             |
| 3      | Lien Lezer           | Lezer   | aanmaken in stap 15.3 (categorie A) |

### Vijf testboeken

| Nr | Titel                          | Auteur              | Item type | Barcode    |
| -- | ------------------------------ | ------------------- | --------- | ---------- |
| 1  | De Aanslag                     | Harry Mulisch       | BK        | TST00001   |
| 2  | Antifa: The Anti-Fascist Handbook | Mark Bray        | BK        | TST00002   |
| 3  | Hoe word ik mezelf?            | Dirk De Wachter     | BK        | TST00003   |
| 4  | Capital and Ideology           | Thomas Piketty      | BK        | TST00004   |
| 5  | Het verdriet van België        | Hugo Claus          | BK        | TST00005   |

> Pas titels gerust aan; barcodes zijn makkelijker als ze deze structuur volgen voor herkenbaarheid in test.

### Tijdsschema

- 15 min — voorbereiding (15.2 + 15.3 + 15.4)
- 45 min — kernscenario (15.5)
- 15 min — randgevallen (15.6)
- 10 min — opruimen (15.7)

---

## 15.2 Voorbereiding — staff-account voor Sam

> **Wie doet dit?** Alex Admin, via `https://bib-test-intra.marxisme.be`.

- [ ] Login als `kohaadmin`.
- [ ] `Patrons` > `+ New patron` > kies categorie `Medewerker (S)`.
- [ ] Vul in:
  - Surname: `Staff`
  - First name: `Sam`
  - Card number: `STAFF001`
  - Library: `SAF`
  - Username: `sam`
  - Password: kies een sterk testwachtwoord (minstens 8 tekens, hoofdletter + cijfer)
- [ ] Klik `Save`.
- [ ] Op detailpagina: klik `More` > `Set permissions`.
- [ ] Vink aan: `catalogue`, `circulate`, `borrowers`, `reserveforothers`, `updatecharges`, `editcatalogue`.
- [ ] Klik `Save`.
- [ ] **Verificatie:** open een privé-browservenster, login op `https://bib-test-intra.marxisme.be` als `sam`. Login moet slagen en de circulation-pagina moet zichtbaar zijn.

---

## 15.3 Voorbereiding — lezer aanmaken voor Lien

> **Wie doet dit?** Sam Staff (in privé-browservenster), of Alex.

- [ ] Login als `sam`.
- [ ] `Patrons` > `+ New patron` > kies categorie `Volwassene (A)`.
- [ ] Vul in:
  - Surname: `Lezer`
  - First name: `Lien`
  - Date of birth: bv. `1990-05-15`
  - Address, City, ZIP: vrij invullen
  - Primary email: gebruik een testadres dat je kunt bereiken
  - Card number: `READER001`
  - Library: `SAF`
  - Username: `lien`
  - Password: kies een sterk testwachtwoord
- [ ] Klik `Save`.
- [ ] **Verificatie:** open een derde privé-browservenster, ga naar `https://bib-test.marxisme.be`, login als `lien`. Moet werken; toont leeg account.

---

## 15.4 Voorbereiding — vijf boeken catalogiseren

> **Wie doet dit?** Sam Staff.

Voor elk boek (1 t/m 5):

- [ ] `Cataloging` > `+ New record` > `MARC21 Default Framework`.
- [ ] Vul minimaal in:
  - Tag `245$a` — Titel.
  - Tag `100$a` — Auteur (achternaam, voornaam).
- [ ] Klik `Save`.
- [ ] In het 'Add item' formulier:
  - Item type: `BK`
  - Home library: `SAF`
  - Barcode: `TST00001` t/m `TST00005`
- [ ] Klik `Add item`.

**Verificatie aan het eind:**

- [ ] Ga naar `Search` > zoek op "Mulisch" → record verschijnt.
- [ ] Open één record, tab `Holdings` → exemplaar staat als `Available`.
- [ ] Herhaal voor minstens twee andere boeken.

---

## 15.5 Kernscenario — het volledige uitleenproces

### Stap 1: Eerste uitlening (Sam aan Lien)

> **Wie:** Sam Staff (staff-interface).

- [ ] `Circulation` (hoofdmenu).
- [ ] Typ in zoekbalk: `READER001` (of "Lien Lezer").
- [ ] Op patron-pagina: tabblad 'Check out' opent automatisch.
- [ ] Scan / typ barcode `TST00001`. Druk Enter.
- [ ] **Verifieer:** boek verschijnt in 'Checked out' tabel met vervaldatum.
- [ ] **Verwachte vervaldatum:** vandaag + 21 dagen (volgens regel `SAF/A/BK` in [doc 13 § 13.5](./13-circulatieregels-matrix.md)).
- [ ] Genoteerde vervaldatum: ___________________

### Stap 2: Tweede en derde uitlening (Lien grenstest)

- [ ] Scan `TST00002` → moet werken.
- [ ] Scan `TST00003` → moet werken.
- [ ] **Verifieer:** Lien heeft nu 3 boeken open.

### Stap 3: OPAC-controle (Lien ziet eigen leningen)

> **Wie:** Lien Lezer (OPAC, derde browservenster).

- [ ] Refresh `https://bib-test.marxisme.be` of klik `your summary`.
- [ ] **Verifieer:** tab 'Checked out' toont 3 boeken met vervaldatum.

### Stap 4: Reservering plaatsen via OPAC

> **Wie:** Lien Lezer.

- [ ] Zoek het 4e boek (`TST00004` — Piketty).
- [ ] Klik op de titel.
- [ ] Klik `Place hold`.
- [ ] Pickup library: `SAF`. Klik `Confirm hold`.
- [ ] **Verifieer:** tab 'Holds' op het OPAC-account toont de reservering met status 'Pending'.

> **Verwachting:** dit boek is beschikbaar op de plank, dus bij inname triggert de hold meteen. Maar omdat het boek nog niet uitgeleend is, blijft het op pending. Dit is normaal — Koha wacht tot het ingenomen wordt of tot iemand het uitleent.

### Stap 5: Verlengen via OPAC

> **Wie:** Lien Lezer.

- [ ] Tab 'Checked out'.
- [ ] Bij `TST00001`, klik `Renew`.
- [ ] **Verifieer:** nieuwe vervaldatum = oude + 21 dagen. Renewals counter staat op 1/2.
- [ ] Klik nogmaals `Renew` voor `TST00001`.
- [ ] **Verifieer:** counter staat op 2/2.
- [ ] Klik nogmaals `Renew` (3e poging).
- [ ] **Verwachting:** **dit moet falen** met melding "too many renewals" of vergelijkbaar.

### Stap 6: Verlengen aan de balie

> **Wie:** Sam Staff.

- [ ] Open Lien's patron-pagina.
- [ ] Tab 'Checkouts'.
- [ ] Klik `Renew` naast `TST00002`. Werkt.
- [ ] Klik `Renew` naast `TST00003`. Werkt.

### Stap 7: Inname (check-in)

> **Wie:** Sam Staff.

- [ ] `Circulation` > `Check in`.
- [ ] Scan `TST00001`. Druk Enter.
- [ ] **Verifieer:** groen vinkje, geen pop-up (geen hold op dit boek).
- [ ] **Verifieer:** Lien's account toont nog 2 leningen (TST00002, TST00003).
- [ ] Scan `TST00004`. Druk Enter.
- [ ] **Verwachting:** **pop-up "Hold found"** want Lien heeft hierop een hold.

> **Wat te doen met de pop-up:** afhankelijk van workflow → "Confirm hold" om het apart te leggen, of "Confirm and print" voor hold slip.

### Stap 8: Uitlenen aan Lien van haar eigen hold

> **Wie:** Sam Staff.

- [ ] Ga terug naar Circulation > Lien's account.
- [ ] Tab 'Holds' op het patron-record toont de waiting hold.
- [ ] Tab 'Check out': scan `TST00004`.
- [ ] **Verifieer:** uitlening werkt, hold wordt automatisch verwijderd.

### Stap 9: Te late inname simuleren

> **Wie:** Alex Admin (vereist sysadmin-toegang).

Dit kan niet via UI. Twee opties:

**Optie A — Wachten:** sla over.

**Optie B — Database direct (alleen test-omgeving!):**

```sql
-- Verbind als root met de Koha-database
mysql koha_<instance>
-- Vervaldatum van TST00002 in het verleden zetten
UPDATE issues
SET date_due = DATE_SUB(NOW(), INTERVAL 5 DAY)
WHERE itemnumber = (SELECT itemnumber FROM items WHERE barcode = 'TST00002');
```

> **Belangrijk:** doe dit nooit in productie. Alleen in test-omgeving.

- [ ] Inname als sam: scan `TST00002`.
- [ ] **Verifieer:** boete verschijnt op Lien's account ('Accounting' tab).
- [ ] **Verwachte boete:** 4 dagen × €0,10 = €0,40 (na 1 dag grace period).

### Stap 10: Boete kwijtschelden

> **Wie:** Sam Staff.

- [ ] Lien's patron-pagina > tab `Accounting`.
- [ ] Vink boete aan.
- [ ] Klik `Write off selected`.
- [ ] **Verifieer:** boete is afgeschreven; saldo terug op €0.

### Stap 11: Laatste boek innemen

> **Wie:** Sam Staff.

- [ ] Inname `TST00003` en `TST00004`.
- [ ] **Verifieer:** Lien's leningen tabel is leeg.

---

## 15.6 Randgevallen (optioneel maar aanbevolen)

### Test 1: Lener boven max checkouts

> Aanbevolen regel staat 'Current checkouts allowed' op 10 voor categorie A.

- [ ] Maak nog 11 testboeken aan (`TST00006` t/m `TST00016`).
- [ ] Leen ze allemaal aan Lien uit.
- [ ] **Verwachting:** bij het 11e boek krijg je waarschuwing "checkout count exceeded" of de checkout wordt geblokkeerd.

### Test 2: Tweede lezer met categorie J

- [ ] Maak een tweede lezer aan: `Jonas Jeugd`, categorie `J`, geboortedatum recent (bv. 2012).
- [ ] Leen `TST00001` uit.
- [ ] **Verifieer:** vervaldatum = 21 dagen (volgens SAF/J/BK regel).
- [ ] Simuleer 5 dagen te laat (zie stap 9).
- [ ] **Verifieer:** boete = (5-3 grace) × €0,05 = €0,10. (Lagere boete, langere grace period voor jeugd.)

### Test 3: Wachtwoord-reset via OPAC

- [ ] Logout Lien.
- [ ] Op OPAC: klik 'Forgot your password?'.
- [ ] Typ `lien` of het e-mailadres.
- [ ] **Verifieer:** e-mail komt aan op het opgegeven testadres met resetlink.

> Als geen e-mail aankomt: zie [doc 10 — Troubleshooting](./10-troubleshooting.md) voor mailconfiguratie.

### Test 4: OPAC-zelf-wijziging gegevens

- [ ] Lien wijzigt haar telefoonnummer via OPAC > 'your personal details'.
- [ ] **Verifieer:** wijziging staat 'pending' (afhankelijk van `OPACPatronDetails`-instelling).
- [ ] Sam Staff: `Patrons` > 'Patrons requesting modifications' → goedkeuren.
- [ ] **Verifieer:** wijziging is doorgevoerd.

### Test 5: Hold annuleren via OPAC

- [ ] Lien plaatst hold op `TST00005`.
- [ ] Lien gaat naar tab 'Holds' > klikt `Cancel`.
- [ ] **Verifieer:** hold is weg.

---

## 15.7 Opruimen na test

Optioneel — afhankelijk of je de testdata wilt bewaren of niet.

- [ ] Verwijder testleningen (alle innames moeten al gedaan zijn).
- [ ] Verwijder of anonimiseer testlezers via `Tools > Patrons (anonymize, bulk-delete)`.
- [ ] Verwijder testrecords via Cataloging (zoek op `TST*` barcodes).
- [ ] Reset Sam Staff naar inactief of verwijder.

---

## 15.8 Resultaten-template

| Stap | Onderdeel                          | Status (✓/✗) | Opmerking |
| ---- | ---------------------------------- | ------------ | --------- |
| 1    | Eerste uitlening, vervaldatum klopt|              |           |
| 2    | Tweede/derde uitlening              |              |           |
| 3    | Lezer ziet leningen op OPAC        |              |           |
| 4    | Hold plaatsen via OPAC              |              |           |
| 5a   | Verlengen via OPAC werkt           |              |           |
| 5b   | 3e renewal wordt geblokkeerd       |              |           |
| 6    | Verlengen aan balie                 |              |           |
| 7a   | Inname zonder hold                  |              |           |
| 7b   | Inname met hold pop-up              |              |           |
| 8    | Uitlenen na hold                    |              |           |
| 9    | Boete bij te late inname            |              |           |
| 10   | Boete kwijtschelden                 |              |           |
| 11   | Laatste innames                     |              |           |
| R1   | Max checkouts                       |              |           |
| R2   | Jeugd-tarieven                      |              |           |
| R3   | Wachtwoord-reset e-mail             |              |           |
| R4   | OPAC zelf-wijziging                 |              |           |
| R5   | Hold annuleren via OPAC             |              |           |

---

## 15.9 Wat als iets faalt?

1. **Noteer welke stap, welke foutmelding.**
2. Check [doc 12 § 12.4 — Veelvoorkomende problemen](./12-klikpaden-stap-voor-stap.md).
3. Check [doc 13 § 13.8 — Verificatie & debugging](./13-circulatieregels-matrix.md).
4. Check de Koha logs: `/var/log/koha/<instance>/`.
5. Voor systeem/infrastructuur problemen: zie [doc 10 — Troubleshooting](./10-troubleshooting.md).
