# 11. Uitleenproces & rollen

Dit document beschrijft op hoog niveau hoe het uitleenproces in Koha 25.05 werkt en welke rol welke verantwoordelijkheid en rechten heeft.

Voor stap-voor-stap klikpaden, zie [doc 12](./12-klikpaden-stap-voor-stap.md).
Voor de circulatieregels-matrix in detail, zie [doc 13](./13-circulatieregels-matrix.md).
Voor visuele weergave van de processen, zie [doc 16](./16-visuele-diagrammen.md).

---

## 11.1 Begrippenlijst

Koha gebruikt eigen terminologie die afwijkt van wat je intuïtief zou verwachten.

| Onze term       | Koha-term                       | Toelichting                                                                    |
| --------------- | ------------------------------- | ------------------------------------------------------------------------------ |
| Admin           | **Superlibrarian**              | Volledige toegang. In dit project: account `kohaadmin`. |
| Staff           | **Library staff** (patron type "Staff") | Geen enkele rol; verzameling permissieflags. Patron categorie `S` (Medewerker). |
| Lezer           | **Patron** (of *borrower*)      | Lid van de bibliotheek. Patron categorie `A` (Volwassene) of `J` (Jeugd). |
| Uitleenbalie    | **Circulation desk**            | De plek in de staff-interface waar uitlenen, innemen, verlengen gebeurt. |
| Staff-interface | **Intranet** of **Staff client** | `https://bib-intra.marxisme.be` (prod) / `https://bib-test-intra.marxisme.be` (test). |
| Lezer-interface | **OPAC**                        | `https://bib.marxisme.be` (prod) / `https://bib-test.marxisme.be` (test). |
| Uitlening       | **Checkout** of **issue**       | Het uitlenen van een exemplaar. |
| Inname          | **Check-in** of **return**      | Terugbrengen van een exemplaar. |
| Reservering     | **Hold** (of *reserve*)         | Lezer legt claim op een titel/exemplaar. |
| Vestiging       | **Library** of **branch**       | Fysieke locatie. In dit project: `SAF` (Steunpunt Antifacisme). |
| Lenercategorie  | **Patron category**             | `S`, `A`, of `J`. Bepaalt mede de circulatieregels. |
| Exemplaartype   | **Item type**                   | Actief: `BK` (Boek). `DVD` en `CD` zijn voorbereid maar uitgecommentarieerd. |
| Circulatieregels | **Circulation and fine rules**  | Matrix van regels per branch × patron category × item type. |

> **Belangrijk:** alle staff zijn ook patrons. Een medewerker is een patron met categorie `S` plus toegekende permissies.

---

## 11.2 Het proces in zes stappen

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  1. Inschrijving │ ──► │ 2. Zoeken/Reserv │ ──► │   3. Uitlenen    │
│   (registratie)  │     │   (OPAC of desk) │     │ (Circulation desk)│
└──────────────────┘     └──────────────────┘     └─────────┬────────┘
                                                            │
                                                            ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ 6. Boetes/Lost   │ ◄── │   5. Inname      │ ◄── │  4. Verlengen    │
│   (indien nodig) │     │  (Circulation)   │     │ (OPAC of desk)   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

Voor visuele versie: zie [doc 16, diagram 1](./16-visuele-diagrammen.md#diagram-1-uitleenproces-in-zes-stappen).

| # | Stap | Wie doet het | Waar |
|---|------|--------------|------|
| 1 | Inschrijving | Staff | Balie (intranet) |
| 2 | Zoeken & reserveren | Lezer (of staff) | OPAC of intranet |
| 3 | Uitlenen | Staff | Balie (intranet) |
| 4 | Verlengen | Lezer of staff | OPAC of intranet |
| 5 | Inname | Staff | Balie (intranet) |
| 6 | Boetes & verloren | Staff (kwijtschelden), Koha (auto-berekening) | Balie (intranet) |

---

## 11.3 De drie rollen

### 11.3.1 Admin (`kohaadmin`)

**Wie:** systeem-eigenaar — engineer en eventueel bibliotheekverantwoordelijke.

**Verantwoordelijkheden:**

- Initiële configuratie van Koha (al grotendeels via Ansible — zie roles `koha_business_*`).
- Inrichten en wijzigen van de circulatieregels-matrix.
- Aanmaken van staff-accounts en toekennen van permissies.
- Onderhoud: backups, updates, monitoring, e-mailbezorging.
- Configuratie van notices (e-mails over te late inname, reserveringen klaar, etc.).
- Bij uitbreiding naar meerdere vestigingen: aanvullen van `koha_business_libraries` defaults.

**Rechten:**

- Permissieflag: `superlibrarian` (één vlag → alle rechten).
- Toegang tot **alle** modules.
- Kan circulatieregels en system preferences wijzigen — dit is wat hen onderscheidt van staff.

> **In dit project:** veel admin-werk is geautomatiseerd. Wijzig configuratie bij voorkeur via Ansible defaults zodat het reproduceerbaar blijft. Zie ook [doc 4](./04-ansible-roles.md) en [doc 7](./07-bibliotheekconfiguratiegids.md).

---

### 11.3.2 Staff (categorie `S`)

**Wie:** medewerkers aan de balie. Bij start van het project mogelijk 1-3 personen.

**Verantwoordelijkheden:**

- Lezers inschrijven, lezergegevens bijwerken.
- Boeken uitlenen, innemen, verlengen aan de balie.
- Reserveringen plaatsen voor lezers die bellen of langskomen.
- Boetes innen of kwijtschelden.
- Catalogiseren van nieuwe exemplaren (afhankelijk van rolverdeling).
- Eenvoudige rapporten draaien (bv. te late innames lijst).

**Rechten — typische combinatie voor balie-medewerker:**

| Permissieflag         | Geeft toegang tot                                                                |
| --------------------- | -------------------------------------------------------------------------------- |
| `catalogue`           | **Verplicht** voor staff-login. Catalogus bekijken in staff-interface. |
| `circulate`           | Volledige toegang tot uitlenen, innemen, verlengen. |
| `borrowers`           | Lezergegevens bekijken, toevoegen, bewerken (met `edit_borrowers` sub-flag). |
| `reserveforothers`    | Reserveringen plaatsen voor lezers. |
| `updatecharges`       | Boetes/kosten beheren (innen, kwijtschelden). |
| `editcatalogue`       | Optioneel — alleen voor staff die mogen catalogiseren. |
| `tools`               | Toegang tot tools-module (selectief sub-permissies geven). |
| `reports`             | Rapporten draaien (alleen-lezen). |

**Wat staff NIET mag:**

- System preferences wijzigen.
- Circulatieregels wijzigen.
- Andere staff-permissies aanpassen.

> Permissies zijn modulair. Je kunt `circulate` als geheel toekennen, of klikken op "Show details" en alleen sub-permissies aanvinken. Voor een eerste staff-account kun je de hele `circulate` vlag aanzetten.

---

### 11.3.3 Lezer (categorie `A` of `J`)

**Wie:** lid van de bibliotheek. Geen toegang tot de staff-interface, alleen tot de OPAC.

**Wat kan een lezer via OPAC:**

- Catalogus doorzoeken (zonder inloggen al mogelijk).
- Inloggen met lidnummer + wachtwoord.
- Eigen account bekijken: huidige uitleningen, openstaande boetes, reserveringen.
- Reserveringen plaatsen op titels/exemplaren.
- Verlengen (afhankelijk van circulatieregels).
- Eigen gegevens bijwerken (afhankelijk van system preferences — zie [doc 14](./14-opac-sysprefs.md)).
- Wachtwoord wijzigen.
- Boekenplanken (lijsten) maken.

**Rechten:**

- **Geen Koha-permissieflags.** Een lezer is "gewoon" een patron zonder staff-flags.
- Toegang en gedrag worden bepaald door OPAC-system preferences (zie [doc 14](./14-opac-sysprefs.md)).

**Wat staff doet voor een lezer:**

- Inschrijven (eerste keer).
- Wachtwoord resetten (bij vergeten wachtwoord, als geen e-mail-reset).
- Lenercategorie wijzigen (bv. `J` → `A` bij 18 jaar).
- Restricties opleggen (bv. tijdelijke blokkade bij wangedrag of openstaande boete).

---

## 11.4 Rollen-permissie matrix

| Actie                                  | Admin | Staff | Lezer           |
| -------------------------------------- | ----- | ----- | --------------- |
| System preferences wijzigen            | ✓     | ✗     | ✗               |
| Circulatieregels wijzigen              | ✓     | ✗     | ✗               |
| Vestigingen / itemtypes beheren        | ✓     | ✗     | ✗               |
| Staff-accounts beheren                 | ✓     | ✗     | ✗               |
| Lezer inschrijven                      | ✓     | ✓     | ✗ (self-register staat uit) |
| Boek uitlenen aan balie                | ✓     | ✓     | ✗               |
| Boek innemen                           | ✓     | ✓     | ✗               |
| Verlengen aan balie                    | ✓     | ✓     | ✗               |
| Verlengen via OPAC                     | n.v.t | n.v.t | ✓ (indien toegestaan) |
| Reservering plaatsen voor anderen      | ✓     | ✓     | ✗               |
| Eigen reservering plaatsen via OPAC    | n.v.t | n.v.t | ✓               |
| Boete kwijtschelden                    | ✓     | ✓     | ✗               |
| Catalogus bekijken                     | ✓     | ✓     | ✓               |
| Catalogiseren (nieuwe records)         | ✓     | ✓ (mits flag) | ✗       |
| Eigen gegevens inzien/wijzigen via OPAC| n.v.t | n.v.t | ✓               |
| Rapporten draaien                      | ✓     | ✓ (mits flag) | ✗       |

Voor visuele versie: zie [doc 16, diagram 2](./16-visuele-diagrammen.md#diagram-2-rollen-en-rechten).

---

## 11.5 Volgorde van inrichten in dit project

De infrastructuur wordt door Ansible gedaan. Wat blijft er voor de operator over:

1. Eerste login als `kohaadmin` op `https://bib-intra.marxisme.be` met wachtwoord uit [doc 1.3](./01-projectoverzicht.md).
2. Verifieer dat branches, patron categorieën en item types correct zijn aangemaakt (uit Ansible roles).
3. Doorloop circulatieregels — zie [doc 13](./13-circulatieregels-matrix.md).
4. Maak eerste staff-account aan voor de baliemedewerker — zie [doc 12 § A7](./12-klikpaden-stap-voor-stap.md).
5. Voer testscenario uit met 3 personen + 5 boeken — zie [doc 15](./15-testscenario.md).
6. OPAC-instellingen verifiëren — zie [doc 14](./14-opac-sysprefs.md).

---

## 11.6 Wat is nieuw in 25.05

- **Check-out optie in zoekbalk** op de hoofdpagina van Circulation — vanuit elke zoekopdracht direct doorklikken naar uitlenen.
- **Renewal settings icon** op de Renew-pagina — datepicker is niet meer altijd zichtbaar; klik op het icoontje om aangepaste vervaldatum in te stellen.
- **Expired hold charge** kan nu in de circulatieregels per regel ingesteld worden (niet alleen via system preference).
- **Hold pickup delay** als kolom in de circulatieregels-matrix (granulariteit per regel ipv alleen system preference).
- **No renewal before** is gesplitst in **No renewal before** en **No automatic renewal before**.
- Extra velden mogelijk op libraries, credit types en debit types.
