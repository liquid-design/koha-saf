# 12. Klikpaden per handeling

Dit document bevat stap-voor-stap instructies voor de belangrijkste acties in het uitleenproces, geordend per rol.

Context: Koha 25.05 op `https://bib-intra.marxisme.be` (staff) en `https://bib.marxisme.be` (OPAC). Voor test-omgeving vervang `bib` door `bib-test`.

> **Notatie:** `Menu > Submenu > Item` betekent: klik op "Menu", dan "Submenu", dan "Item". Velden uit de UI staan tussen 'aanhalingstekens'.

---

## 12.1 ADMIN — klikpaden

> Veel admin-werk is in dit project geautomatiseerd via Ansible. De stappen hieronder zijn voor handmatige verificatie of aanpassing. Voor structurele wijzigingen: pas de Ansible defaults aan en draai het bijbehorende playbook opnieuw.

### A1. Vestiging (library) toevoegen

**Geautomatiseerd via:** `koha_business_libraries` role.

Handmatig:
1. Login als `kohaadmin`.
2. `Administration` > `Libraries` (onder 'Basic parameters').
3. Klik `+ New library`.
4. Vul minimaal in:
   - 'Library code' — kort, uniek, max 10 tekens (bv. `SAF`).
   - 'Name' — volledige naam (bv. `Steunpunt Antifacisme`).
5. Vul optioneel adres, telefoon, e-mail, opening hours in.
6. Klik `Submit`.

### A2. Lenercategorie toevoegen

**Geautomatiseerd via:** `koha_business_patron_categories` role.

Handmatig:
1. `Administration` > `Patron categories`.
2. Klik `+ New category`.
3. Vul in:
   - 'Category code' — kort, uniek (bv. `A`).
   - 'Description' — bv. `Volwassene`.
   - 'Category type' — kies: `Adult`, `Child`, `Staff`, `Organization`, `Statistical`, `Professional`.
   - 'Enrollment period' — geldigheidsduur.
4. Klik `Save`.

### A3. Itemtype toevoegen

**Geautomatiseerd via:** `koha_business_item_types` role.

Handmatig:
1. `Administration` > `Item types`.
2. Klik `+ New item type`.
3. Vul in:
   - 'Item type' — code (bv. `BK`).
   - 'Description' — bv. `Boek`.
   - 'Default replacement cost' — vervangingskosten.
4. Klik `Save changes`.

### A4. Circulatieregels instellen

**Geautomatiseerd via:** `koha_business_circulation` role.

Voor de matrix in detail en hoe je deze leest: zie [doc 13](./13-circulatieregels-matrix.md).

Handmatig:
1. `Administration` > `Circulation and fine rules`.
2. Bovenaan: kies bij 'Select a library' → `Standard rules for all libraries` of `SAF`.
3. Onderaan in de tabel zie je een regel-bouwer. Vul de waarden in zoals beschreven in doc 13.
4. Klik `Save` aan het eind van de regel.

### A5. System preferences voor circulation

**Deels geautomatiseerd via:** `koha_business_sysprefs` role.

Voor circulatie-gerelateerde sysprefs:
1. `Administration` > `System preferences`.
2. Klik op `Circulation` in de linkerkolom.
3. Belangrijkste:
   - `AutoReturnCheckedOutItems`, `AllowFineOverride`, `AllowItemsOnHoldCheckout`.
   - `useDaysMode` — hoe omgaan met sluitingsdagen voor vervaldatum.
   - `WaitingNotifyAtCheckout` — pop-up als lezer wachtende reserveringen heeft.

Voor OPAC-gerelateerde sysprefs (lezer-gedrag): zie [doc 14](./14-opac-sysprefs.md).

### A6. Kalender (sluitingsdagen) instellen

1. `Tools` > `Calendar` (onder 'Additional tools').
2. Selecteer de juiste vestiging boven de kalender (`SAF`).
3. Klik op een datum die gesloten is.
4. Vul in:
   - 'Title' — bv. `Kerstmis`.
   - 'Reason' — vrij tekstveld.
   - Kies type: 'One-time event', 'Holiday repeating yearly', etc.
5. Klik `Save`.

> **Effect:** afhankelijk van system preference `useDaysMode` worden vervaldatums automatisch verschoven.

### A7. Staff-account aanmaken (handmatig)

**Geautomatiseerd via:** `koha_business_staff` role (voor het standaard team).

Handmatig — twee stappen:

**Stap 1 — Patron aanmaken:**

1. `Patrons` > `+ New patron`.
2. Kies categorie: `Medewerker (S)`.
3. Vul minimaal in:
   - 'Surname', 'First name'.
   - 'Card number'.
   - 'Library' — `SAF`.
   - In 'Library use' sectie: 'Username' en 'Password'.
4. Klik `Save`.

**Stap 2 — Permissies toekennen:**

1. Op patron-detailscherm: klik `More` > `Set permissions`.
2. Vink aan:
   - `catalogue` — **verplicht** voor staff login.
   - `circulate`.
   - `borrowers`.
   - `reserveforothers`.
   - `updatecharges`.
   - `editcatalogue` (optioneel).
3. Klik `Save`.

### A8. Notices controleren

1. `Tools` > `Notices and slips`.
2. Belangrijkste notices:
   - `OVERDUE` — herinnering te late inname.
   - `HOLD` — reservering klaar voor afhalen.
   - `CHECKIN` — bevestiging inname.
   - `CHECKOUT` — bevestiging uitlening.
3. Klik `Edit` om template aan te passen. Gebruik placeholders zoals `<<borrowers.firstname>>`, `<<items.barcode>>`, `<<biblio.title>>`.
4. Klik `Submit`.

---

## 12.2 STAFF — klikpaden

### S1. Inloggen

1. Ga naar `https://bib-intra.marxisme.be`.
2. Vul username en password in.
3. Kies vestiging in dropdown 'Library' → `SAF`.
4. Klik `Login`.

### S2. Lezer inschrijven

1. `Patrons` > `+ New patron`.
2. Kies categorie:
   - `Volwassene (A)` voor 18+.
   - `Jeugd (J)` voor onder de 18.
3. Vul in:
   - 'Surname', 'First name', 'Date of birth'.
   - 'Address', 'City', 'ZIP/Postal code'.
   - 'Primary email', 'Primary phone'.
   - 'Card number' — meestal automatisch.
   - 'Library' — `SAF`.
   - In 'OPAC/Staff interface login' sectie: 'Username' + 'Password'.
4. Klik `Save`.

### S3. Boek uitlenen (checkout)

**Methode 1 — vanuit hoofdmenu:**

1. Klik `Circulation`.
2. In de zoekbalk bovenaan: typ het lidnummer.
3. Op het patron-scherm verschijnt automatisch het tabblad 'Check out'.
4. Scan de barcode in 'Checking out to ...'. Druk Enter.
5. Het exemplaar verschijnt in de tabel `Checked out` met vervaldatum.

**Methode 2 — vanuit zoekbalk (nieuw in 25.05):**

1. In de zoekbalk bovenaan staat een 'Check out' optie. Selecteer deze.
2. Typ naam of lidnummer.
3. Klik op de juiste lezer; je komt direct in 'Check out' tab.

> **Mogelijke waarschuwingen:**
> - Boete openstaand → klik `Yes, check out` om door te gaan.
> - Item is gereserveerd voor andere lezer → kies actie.
> - Lezer heeft restrictie → niet doorgaan zonder admin-overleg.

### S4. Boek innemen (check-in)

1. `Circulation` > `Check in`.
2. Scan de barcode. Druk Enter.
3. Resultaat:
   - Groen vinkje + lezergegevens → succesvolle inname.
   - Pop-up "Hold found" → exemplaar gereserveerd voor iemand anders → leg apart op de hold-plank.

### S5. Verlengen aan de balie

**Methode 1 — vanuit lezer-account:**

1. Open patron-detailpagina.
2. Tabblad 'Checkouts' is standaard zichtbaar.
3. Klik `Renew` naast het juiste boek, of vink meerdere aan en klik `Renew or check in selected items`.

**Methode 2 — via Renew-pagina:**

1. `Circulation` > `Renew`.
2. Klik het 'renewal settings' icoontje voor aangepaste vervaldatum (nieuw in 25.05 — datepicker is verborgen tot je hierop klikt).
3. Stel desgewenst een datum in.
4. Scan barcode.

### S6. Reservering plaatsen voor een lezer

1. Zoek het bibliografische record.
2. Open het record.
3. Klik `Place hold`.
4. Vul in:
   - 'Patron' — typ naam of lidnummer.
   - 'Pickup library' — `SAF`.
   - Optioneel: 'Hold expires on', 'Specific item'.
5. Klik `Place hold`.

### S7. Boete kwijtschelden of betalen

1. Open patron-detailpagina.
2. Tabblad `Accounting`.
3. **Betalen:**
   - Vink boete(s) aan.
   - Klik `Pay amount` of `Pay selected`.
   - Vul bedrag in, klik `Confirm`.
4. **Kwijtschelden:**
   - Vink aan.
   - Klik `Write off selected`.
   - Bevestig.

### S8. Lezerwachtwoord resetten

1. Open patron-detailpagina.
2. Klik `More` > `Change password`.
3. Vul nieuw wachtwoord in (2x).
4. Klik `Save`.
5. Communiceer wachtwoord via veilig kanaal.

### S9. Status van een boek bekijken

1. Zoek het record.
2. Open record.
3. Tab 'Holdings' toont alle exemplaren.
4. Per exemplaar zichtbaar:
   - Status (Available, Checked out tot dd/mm/yyyy, On hold, In transit, Lost).
   - Home library, Current location, Item type, Call number.

### S10. Boek catalogiseren

Zie ook [doc 7 § 7.4 — Eerste boek catalogiseren](./07-bibliotheekconfiguratiegids.md).

1. `Cataloging` > `+ New record` > `MARC21 Default Framework`.
2. Vul minimaal in:
   - `245$a` — Titel.
   - `100$a` — Auteur.
3. Klik `Save`.
4. Voeg item toe: vul item type `BK`, vestiging `SAF` in.
5. Barcode wordt automatisch gegenereerd.

---

## 12.3 LEZER — klikpaden (OPAC)

### L1. Inloggen op OPAC

1. Ga naar `https://bib.marxisme.be`.
2. Klik `Log in to your account`.
3. Vul lidnummer + password in.
4. Klik `Log in`.

### L2. Catalogus doorzoeken

1. Op de OPAC homepage: zoekbalk bovenaan.
2. Kies dropdown links: 'Library catalog', 'Title', 'Author', etc.
3. Typ zoekterm > Enter.
4. Resultaten verschijnen; verfijn links met facetten.

### L3. Reservering plaatsen

1. Klik op een titel in de zoekresultaten.
2. Op de detailpagina: klik `Place hold`.
3. Optioneel: 'Pickup location' → `SAF`.
4. Optioneel: 'Hold not needed after'.
5. Klik `Confirm hold`.

### L4. Eigen uitleningen bekijken

1. Ingelogd: klik op je naam rechtsboven > `your summary`.
2. Tabblad `Checked out` toont huidige uitleningen met vervaldatum.
3. Tabblad `Holds` toont reserveringen.
4. Tabblad `Charges` toont openstaande boetes.

### L5. Verlengen via OPAC

1. Tabblad `Checked out`.
2. Achter elk boek staat een `Renew` knop.
3. Klik `Renew`.
4. Bevestiging of error verschijnt:
   - Succesvol → nieuwe vervaldatum zichtbaar.
   - Niet toegestaan → reden wordt getoond.

> Werkt alleen als `OpacRenewalAllowed` ingeschakeld is. Zie [doc 14](./14-opac-sysprefs.md).

### L6. Wachtwoord wijzigen

1. Ingelogd: klik je naam rechtsboven > `your personal details` > `change your password`.
2. Vul oud + nieuw wachtwoord (2x) in.
3. Klik `Submit changes`.

### L7. Reservering annuleren

1. Tabblad `Holds`.
2. Naast elke reservering: `Cancel` knop.
3. Bevestig.

---

## 12.4 Veelvoorkomende problemen

| Probleem | Mogelijke oorzaak | Oplossing |
| -------- | ----------------- | --------- |
| "Cannot check out" bij uitlenen | Geen circulatieregel voor deze combinatie | Admin: voeg regel toe (zie [doc 13](./13-circulatieregels-matrix.md)) |
| Lezer kan niet inloggen op OPAC | Geen username/password ingesteld | Staff: zet username/password in patron record |
| Staff kan niet inloggen op staff-interface | `catalogue` permissie ontbreekt | Admin: zet `catalogue` flag aan |
| Verlengen lukt niet via OPAC | `OpacRenewalAllowed` uit, of max verlengingen bereikt, of hold op item | Admin: zie [doc 14](./14-opac-sysprefs.md) |
| Vervaldatum valt op zondag | `useDaysMode` staat op 'Ignore the calendar' | Admin: zet op 'push to next open day' + kalender invullen (A6) |
| Permissies wijzigen werkt niet | Eigen account heeft geen `permissions` flag | Admin: gebruik `kohaadmin` |

Voor uitgebreidere troubleshooting: zie [doc 10](./10-troubleshooting.md).
