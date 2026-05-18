# 13. Circulatieregels-matrix in detail

Dit document legt het hart van Koha uit — de circulatieregels-matrix. Wie mag wat lenen, hoelang, hoe vaak verlengen, met welke boetes? Alles wordt hier bepaald.

> **Lees § 13.1 t/m § 13.3 minstens één keer door voordat je iets aanpast.** Een verkeerd ingestelde regel = leningen mislukken zonder duidelijke fout.

Voor visuele uitleg van de specificiteit-evaluatie: zie [doc 16, diagram 3](./16-visuele-diagrammen.md#diagram-3-specificiteit-evaluatie).

---

## 13.1 Wat is de matrix?

De circulatieregels in Koha zijn georganiseerd als een driedimensionale matrix:

```
Branch  ×  Patron category  ×  Item type
```

Per cel kun je een rij regels definiëren: leentermijn, max aantal leningen, boetes, verlengingen, etc.

**In dit project op dit moment:**

| Dimensie         | Aantal waarden    | Waarden                        |
| ---------------- | ----------------- | ------------------------------ |
| Branch           | 1 (uitbreidbaar)  | `SAF`                          |
| Patron category  | 3                 | `S` (Medewerker), `A` (Volwassene), `J` (Jeugd) |
| Item type        | 1 actief          | `BK` (Boek). `DVD` en `CD` voorbereid maar inactief. |

Mogelijk aantal cellen: **1 × 3 × 1 = 3 specifieke regels**, plus de `All/All/All` fallback.

> **Belangrijk:** elke dimensie kan ook `All` zijn, wat betekent: "geldt voor elke waarde in deze dimensie tenzij er een specifiekere regel is".

---

## 13.2 Hoe Koha de matrix leest (specifieker wint)

Koha kiest **altijd** de meest specifieke regel die past. Dit is de evaluatie-volgorde, van meest naar minst specifiek:

1. Specifieke branch + specifieke patron category + specifieke item type
2. Specifieke branch + specifieke patron category + `All` item types
3. Specifieke branch + `All` patron categories + specifieke item type
4. Specifieke branch + `All` + `All`
5. `All` branches + specifieke patron category + specifieke item type
6. `All` + specifieke patron category + `All`
7. `All` + `All` + specifieke item type
8. `All` + `All` + `All`  ← de ultieme fallback

> **Praktische regel:** zorg dat er **altijd** een `All / All / All` fallback bestaat. Anders kunnen combinaties zonder match gewoon falen.

> **Niet verwarren met regelvolgorde in de UI:** de volgorde waarin regels in de matrix-pagina worden getoond bepaalt **niet** welke regel wint. Alleen specificiteit telt.

### Voorbeeld

Stel je hebt deze regels:

| # | Branch | Category | Item type | Loan period |
|---|--------|----------|-----------|-------------|
| 1 | All    | All      | All       | 14 dagen    |
| 2 | SAF    | J        | All       | 21 dagen    |
| 3 | All    | All      | BK        | 14 dagen    |

Een lezer met categorie `J` leent in `SAF` een `BK`. Welke regel wint?

- Regel 2 (SAF + J + All): match op branch en category → **specificiteit 2/3**
- Regel 3 (All + All + BK): match alleen op itemtype → **specificiteit 1/3**
- Regel 1: alleen fallback → specificiteit 0/3

**Regel 2 wint.** Lezer krijgt 21 dagen.

---

## 13.3 Veldreferentie (alle kolommen uit de matrix)

Hieronder elk veld uit de Koha 25.05 matrix, met betekenis en aanbevolen startwaarde voor SAF.

### 13.3.1 Identificatie

| Veld                | Betekenis                                                      | SAF-startwaarde |
| ------------------- | -------------------------------------------------------------- | --------------- |
| Patron category     | Voor welke patron category geldt deze regel                    | varieert        |
| Item type           | Voor welk item type geldt deze regel                           | `BK` of `All`   |
| Note                | Vrij tekstveld om de regel intern te documenteren              | optioneel       |

### 13.3.2 Uitleningen (checkouts)

| Veld                              | Betekenis                                                           | SAF-startwaarde |
| --------------------------------- | ------------------------------------------------------------------- | --------------- |
| Current checkouts allowed         | Max aantal exemplaren dat tegelijk uitgeleend mag zijn              | 20 (S), 10 (A), 5 (J) |
| Current on-site checkouts allowed | Aantal "in-house" leeszaal-uitleningen (apart geteld)               | leeg            |
| Loan period                       | Standaard leentermijn                                               | 14 of 21        |
| Unit                              | `Days` of `Hours`                                                   | `Days`          |
| Hard due date                     | Vaste vervaldatum die "wint" voor of na de berekende datum (zie § 13.4) | leeg       |

### 13.3.3 Boetes (fines)

| Veld                       | Betekenis                                                          | SAF-startwaarde |
| -------------------------- | ------------------------------------------------------------------ | --------------- |
| Fine amount                | Boete per interval te laat                                         | 0,10            |
| Fine charging interval     | Hoe vaak boete aangroeit                                           | 1               |
| When to charge             | `End of interval` of `Start of interval`                           | End of interval |
| Fine grace period (days)   | Aantal dagen "gratis" voor boete begint te lopen                   | 1               |
| Overdue fines cap (amount) | Max totaal boetebedrag voor één lening                             | 5,00            |
| Cap fine at replacement price | Indien aangevinkt: boete kan niet hoger zijn dan vervangingskost  | aanvinken       |

### 13.3.4 Verlengingen (renewals)

| Veld                          | Betekenis                                                           | SAF-startwaarde |
| ----------------------------- | ------------------------------------------------------------------- | --------------- |
| Renewals allowed (count)      | Max aantal verlengingen per uitlening                               | 2               |
| Renewal period                | Duur van één verlenging (meestal gelijk aan loan period)            | 14 of 21        |
| No renewal before             | Aantal dagen vóór vervaldatum vanaf wanneer manueel verlengen mag  | 0 (altijd)      |
| No automatic renewal before   | Idem voor auto-renewal (gesplitst in 25.05)                         | 0               |
| Automatic renewal             | Mag dit automatisch verlengd worden?                                | No              |
| No automatic renewal after (hard limit) | Vaste datum waarna auto-renew niet meer mag                | leeg            |

### 13.3.5 Reserveringen (holds)

| Veld                              | Betekenis                                                           | SAF-startwaarde |
| --------------------------------- | ------------------------------------------------------------------- | --------------- |
| Holds allowed (total)             | Max actieve reserveringen voor deze patron category                 | 5               |
| Holds allowed (daily)             | Max nieuwe reserveringen per dag                                    | 5               |
| Holds per record (count)          | Max reserveringen per bibliografisch record                         | 1               |
| On shelf holds allowed            | Mag een lezer een hold plaatsen op een beschikbaar (op de plank) item? | `If any unavailable` |
| OPAC item level holds             | Mag lezer specifiek exemplaar reserveren via OPAC?                 | `Don't allow`   |
| Holds pickup delay (days)         | **Nieuw in 25.05**: hoe lang mag een gereserveerd item op de hold-plank blijven liggen | 7 |
| Expired hold charge               | **Nieuw in 25.05**: bedrag bij niet-ophalen van hold                | 0               |

### 13.3.6 Diversen

| Veld                                 | Betekenis                                                         | SAF-startwaarde |
| ------------------------------------ | ----------------------------------------------------------------- | --------------- |
| Suspension in days                   | Alternatief voor boete: aantal dagen geblokkeerd                  | leeg            |
| Suspension charging interval         | Per hoeveel dagen te laat → 1 dag suspensie                       | leeg            |
| Max suspension duration              | Max dagen geblokkeerd                                             | leeg            |
| Article requests                     | Mogen artikelaanvragen geplaatst worden?                          | `No`            |
| Rental discount (%)                  | Korting op huurkosten                                             | leeg            |
| Decreased loan period for high holds | Verkorte leentermijn als veel reserveringen op één titel staan    | leeg            |
| Days mode                            | Hoe omgaan met sluitingsdagen (default = system preference `useDaysMode`) | `Default` |

> **Tip:** je hoeft niet elk veld in te vullen. Lege velden = "geen beperking" of "neem de fallback / system preference".

---

## 13.4 Hard due date — wanneer gebruik je dit?

`Hard due date` is een vaste kalenderdatum waarop alle items van deze regel verlopen, ongeacht wanneer ze geleend zijn. Je kiest één van drie modes:

- **Before**: als de berekende vervaldatum na de hard date valt, gebruik de hard date. Zo niet, gebruik de normale berekening.
- **Exactly**: gebruik altijd de hard date.
- **After**: als de berekende vervaldatum vóór de hard date valt, gebruik de hard date.

**Wanneer nuttig:** projecten met een einddatum (bv. zomeruitleen tot 31/8), tijdelijke abonnementen, examenperiode-leningen.

**Voor SAF op dit moment niet nodig** — laat leeg.

---

## 13.5 Aanbevolen startmatrix voor SAF

Onderstaande matrix is een minimum-viable startset. Drie patron categories × één actief item type = vier regels (drie specifieke + één fallback).

### Regel 1 — Fallback (All / All / All)

| Veld                          | Waarde      |
| ----------------------------- | ----------- |
| Branch                        | All         |
| Patron category               | All         |
| Item type                     | All         |
| Current checkouts allowed     | 5           |
| Loan period                   | 14          |
| Unit                          | Days        |
| Fine amount                   | 0,10        |
| Fine charging interval        | 1           |
| Fine grace period             | 1           |
| Overdue fines cap             | 5,00        |
| Renewals allowed              | 1           |
| Renewal period                | 14          |
| Holds allowed (total)         | 3           |
| Holds per record              | 1           |
| On shelf holds allowed        | If any unavailable |

> De fallback is conservatief. Specifiekere regels mogen genereuzer zijn.

### Regel 2 — Volwassene + Boek (SAF / A / BK)

| Veld                          | Waarde      |
| ----------------------------- | ----------- |
| Current checkouts allowed     | 10          |
| Loan period                   | 21          |
| Renewals allowed              | 2           |
| Renewal period                | 21          |
| Holds allowed (total)         | 5           |
| Holds per record              | 1           |
| Fine amount                   | 0,10        |
| Fine grace period             | 1           |
| Overdue fines cap             | 5,00        |

### Regel 3 — Jeugd + Boek (SAF / J / BK)

| Veld                          | Waarde      |
| ----------------------------- | ----------- |
| Current checkouts allowed     | 5           |
| Loan period                   | 21          |
| Renewals allowed              | 2           |
| Renewal period                | 21          |
| Holds allowed (total)         | 3           |
| Holds per record              | 1           |
| Fine amount                   | 0,05        |
| Fine grace period             | 3           |
| Overdue fines cap             | 2,50        |

> Lagere boete + langere grace period voor jeugd = bewuste pedagogische keuze.

### Regel 4 — Medewerker + Boek (SAF / S / BK)

| Veld                          | Waarde      |
| ----------------------------- | ----------- |
| Current checkouts allowed     | 20          |
| Loan period                   | 30          |
| Renewals allowed              | 5           |
| Renewal period                | 30          |
| Holds allowed (total)         | 10          |
| Holds per record              | 1           |
| Fine amount                   | 0           |
| Fine grace period             | leeg        |

> Medewerkers krijgen geen boetes en ruime termijnen — typisch voor interne organisaties.

---

## 13.6 Default values onder de matrix

Onder de hoofdmatrix op de pagina `Administration > Circulation and fine rules` staan extra default-secties die onafhankelijk van de matrix werken:

### 13.6.1 Default checkout, hold and return policy by patron category

Per patron category een algemeen maximum dat over alle item types heen geldt. Bv.: een Volwassene mag 10 boeken + 5 DVD's + 2 CD's lenen, maar het totaal nooit meer dan 12. Dat zet je hier.

### 13.6.2 Default holds policy by item type

Algemene hold-policies per item type, ongeacht patron category.

### 13.6.3 Default open article requests limit

Max aantal openstaande artikelaanvragen per patron category.

### 13.6.4 Default lost item fee refund on return policy

Wat doet Koha als een als-verloren-gemarkeerd item alsnog wordt teruggebracht?

---

## 13.7 Hoe wijzig je een regel?

### Methode 1: via de UI (snel testen)

1. `Administration` > `Circulation and fine rules`.
2. Selecteer bovenaan de juiste branch (`Standard rules for all libraries` of `SAF`).
3. Wijzig een waarde inline → klik `Save` aan het eind van die rij.
4. Of: voeg een nieuwe regel toe via de lege rij onderaan.

### Methode 2: via Ansible (reproduceerbaar — aanbevolen)

De huidige Ansible role `koha_business_circulation` schrijft één set globale defaults via `circulation_rules` tabel. Voor specifiekere regels (per patron category × item type) zou de role uitgebreid moeten worden.

**Huidige defaults zitten in:** `ansible/roles/koha_business_circulation/defaults/main.yml`

```yaml
circ_rule_max_checkouts: 20
circ_rule_loan_period: 14
circ_rule_renewals_allowed: 2
circ_rule_holds_daily: 5
circ_rule_holds_per_record: 3
circ_rule_onshelf: 1
```

Voor matrix-uitbreiding: zie [doc 8 — Beperkingen & Roadmap](./08-beperkingen-roadmap.md).

> Aanbeveling: maak eerst regels in de UI om te testen wat werkt. Codeer ze daarna in Ansible defaults voor reproduceerbaarheid.

---

## 13.8 Verificatie & debugging

### Hoe weet je welke regel toegepast wordt?

Bij een uitlening laat Koha de berekende vervaldatum zien. Klop dat met je matrix. Als het niet overeenkomt:

1. Klopt de patron category van de lezer? (zichtbaar in patron-record).
2. Klopt het item type van het exemplaar? (zichtbaar in holdings-tab).
3. Klopt de branch van de lener / het item / de loggedin staff?
4. Is er een specifiekere regel die je over het hoofd ziet?

### SQL-check

Om alle huidige regels op te lijsten:

```sql
SELECT branchcode, categorycode, itemtype, rule_name, rule_value
FROM circulation_rules
ORDER BY branchcode, categorycode, itemtype, rule_name;
```

`NULL` waarden in `branchcode`/`categorycode`/`itemtype` betekenen "All".

### Veelvoorkomende misverstanden

| Symptoom | Oorzaak |
| -------- | ------- |
| Lezer kan niet lenen, foutmelding "Cannot check out — no rule" | Geen `All/All/All` fallback aanwezig |
| Lezer mag minder lenen dan verwacht | `Default checkout policy by patron category` (§ 13.6.1) staat lager dan de matrix-regel — de laagste wint |
| Boete wordt niet aangerekend | `Fine amount` leeg, of `Fine grace period` te hoog, of system preference `finesMode` staat op `Calculate (but only for mailing to the patron)` |
| Verlenging mislukt 5 dagen voor vervaldatum | `No renewal before` staat op een waarde > 5 |
| Vervaldatum klopt niet met aantal dagen | Days mode + sluitingsdagen-kalender werken anders dan verwacht; check `useDaysMode` system preference |

---

## 13.9 Volgende stappen

- [Doc 14](./14-opac-sysprefs.md) — hoe lezers met deze regels in aanraking komen via OPAC.
- [Doc 15](./15-testscenario.md) — valideer dat jouw matrix doet wat je verwacht.
- [Doc 16](./16-visuele-diagrammen.md) — visuele weergave van de matrix-evaluatie en het volledige proces.
