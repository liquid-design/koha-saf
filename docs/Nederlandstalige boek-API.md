# Nederlandstalige boek-API's — landscape voor koha-saf

Onderzoeksdatum: mei 2026. Gefocust op bronnen die XML/JSON/MARC teruggeven voor ISBN-lookups, met aandacht voor wat in de afgelopen ~2 jaar nog actief is bediscussieerd.

## TL;DR — wat is nieuw t.o.v. je huidige pipeline

Je huidige merge-prioriteit is KB-NL → LoC → BnF → Google Books → OpenLibrary. Er zijn vier bronnen die je nog **niet** hebt, en die voor een AF-collectie potentieel zeer interessant zijn:

1. **Open Vlacc / Cultuurconnect** (Vlaanderen) — Z39.50/SRU op MARC21, dagelijks ververst, ~290 openbare bibliotheken. Vereist apart contact met servicedesk@cultuurconnect.be.
2. **KB SPARQL endpoint** (`data.bibliotheken.nl/sparql`) — Linked Open Data van de Nederlandse Bibliografie Totaal (NBT) onder vrije licentie. Geen rate-limits zoals SRU.
3. **K10plus SRU** (`sru.k10plus.de`) — Duitse PICA-verbundcatalogus, indexeert óók veel Nederlandstalig materiaal omdat universiteiten meedoen. Levert MARCXML/PICA-XML.
4. **Meta4books / Boekenbank** (Vlaanderen) — RESTful Products API + Zoek API, ~1.8M ISBN's, commercieel maar specifiek Vlaams/Nederlands.

---

## 1. Officiële Nederlandse / Vlaamse bibliografische bronnen

### KB SRU (wat je al gebruikt)
- **Endpoint**: `https://jsru.kb.nl/sru/sru`
- **Collecties** (`x-collection`): GGC (wat jij gebruikt voor boeken), DPO, ANP, DBNLA, e.a. Volledige lijst via `?operation=explain`.
- **Schemas**: dcx (Dublin Core extended), didl. recordSchema parameter switcht ertussen.
- **Tutorials**: github.com/KBNLresearch/intro-kb-apis (RUG-workshop) — actief onderhouden, laatste commits in 2024.
- **Python wrapper**: github.com/KBNLresearch/KB-python-API.
- **isbnlib plugin**: `pip install isbnlib-kb` voegt `kb` als provider toe aan isbnlib (versie 0.0.2, 2021 — werkt nog).

### KB SPARQL / Linked Open Data — **NIEUW VOOR JOU**
- **Endpoint**: `http://data.bibliotheken.nl/sparql` (Virtuoso)
- **Named graphs**:
  - `http://data.bibliotheken.nl/nbt/` — Nederlandse Bibliografie Totaal (publicaties)
  - `http://data.bibliotheken.nl/thes/` — Brinkman/GTT trefwoorden
  - `http://data.bibliotheken.nl/nta` — Persoonsnamenthesaurus (Auteursnamen)
  - `http://data.bibliotheken.nl/corps` — Corporatiethesaurus
- **Licentie**: ODC-By (vrije licentie). De GGC-datasets vallen onder OCLC-licentie met naamsvermelding.
- **Format**: JSON, XML, Turtle, RDF/XML — je kiest. Geen SRU-quirks.
- **Bulk dumps**: `https://data.bibliotheken.nl/KB/Production/download.trig.gz?graph=...`
- **Voordeel voor SAF**: snellere subject/author lookups, trefwoordenthesaurus voor je faceted search, geen Dublin Core wrapping-issues. Nadeel: SPARQL = leercurve.

### STCN (Short-Title Catalogue Netherlands)
- Voor boeken **tot 1801** — waarschijnlijk niet relevant voor jullie collectie. Gehost sinds 2023 door CERL (Consortium of European Research Libraries) in Den Haag.

### Open Vlacc (Cultuurconnect) — **ZEER RELEVANT VOOR SAF**
- **Wat**: centrale Vlaamse bibliografische databank. De 6 grootste Vlaamse bibliotheken (Antwerpen, Brugge, Brussel, Gent, Hasselt, Leuven) catalogiseren centraal, sinds 2023 ook Aalst, Brakel, Roeselare, Turnhout, ARhus. Bevat ook Centrale Discotheek Rotterdam en Meta4Books.
- **Aanbod aan derden**: MARC21 via **Z39.50, SRU of dagelijkse export**. Gelicentieerd, dus contact via servicedesk@cultuurconnect.be voor toegang.
- **Twee API-varianten** (Catalogus API):
  - *Vrije API*: titelbeschrijvingen + covers, vrij gebruik
  - *Rijke API*: + ingekochte data (samenvattingen, recensies), enkel niet-commercieel met publieksbereik-functie
- **Status 2024–2026**: Aleph wordt uitgefaseerd in 2026 — Cultuurconnect zoekt nieuw catalografiesysteem. In 2027 vernieuwen ze ook de zoekmotor (partner: Delaware). Verwacht dus dat endpoints/schema's in beweging zijn de komende jaren.
- **Voor SAF**: dit is de meest natuurlijke Vlaamse partner — Steunpunt Antifascisme is een Vlaamse organisatie, en de Open Vlacc zal Nederlandstalige (politieke) literatuur typisch beter beschreven hebben dan KB-NL.

### Nationale Bibliotheekcatalogus (NBC) — Nederland
- Bevat collecties van álle openbare bibliotheken in Nederland + KB + Centrale Discotheek Rotterdam.
- Bevraagbaar via OAI-PMH (`http://services.kb.nl/mdo/oai`) — alleen harvesting, geen losse query-API.
- Indirect bruikbaar via WorldCat (zie verder).

### Meta4books / Boekenbank (Vlaanderen)
- **Wat**: ISBN-kantoor voor Vlaanderen + Brussel, databank met 1.8M ISBN's (Vlaamse én Nederlandse markt).
- **API's**:
  - *Products API*: volledig boekdetail voor één of meer ISBN's (voor dagelijkse updates)
  - *Zoek API*: zoekopdracht in databank, beknopte resultaten
- **Format**: RESTful, JSON/XML (geen publieke spec — krijg je via lidmaatschap)
- **Kost**: lidmaatschap vereist, bedoeld voor uitgevers/boekhandels/bibliotheken
- **Voor SAF**: commercieel, dus voor jullie scope (kleine NGO-bibliotheek) waarschijnlijk overkill — maar als jullie ooit een formele samenwerking met een Vlaamse bibliotheek opzetten kan dit lonen.

### CB (Centraal Boekhuis) / TitelBank — Nederland
- **Titelbank.nl**: officiële NL database met alle uitgegeven boektitels. Geen open API. Sleutelt aan toegang voor partners; voor B2B via CB Online.
- **DANTE**: samenwerking Meta4Books × CB voor metadata-uitwisseling. Geen publieke endpoints.

---

## 2. Internationale catalogi met goede NL/VL-dekking

### K10plus (Duitse PICA verbundcatalogus) — **NIEUW VOOR JOU, ZEER WAARDEVOL**
- **SRU endpoint**: `http://sru.k10plus.de/opac-de-627`
- **Voorbeeld ISBN query**: `?version=1.1&operation=searchRetrieve&query=pica.isb=9789012345678&maximumRecords=10&recordSchema=picaxml`
- **recordSchema-opties**: picaxml, marcxml, mods36
- **Waarom relevant**: K10plus bundelt GBV (Noord-Duitsland) + BSZ (Baden-Württemberg). Veel Duitstalige én Nederlandstalige wetenschappelijke literatuur. Universiteiten in NL/BE leveren ook hierin aan via OCLC/PICA.
- **Bulk dump**: `https://swblod.bsz-bw.de/od/` — 87M MARCXML records, CC0
- **Koha-config** (uit officiële wiki):
  ```
  host: sru.k10plus.de
  port: 80
  db: gvk
  servertype: sru
  syntax: USMARC
  sru_fields: title=pica.tit,isbn=pica.isb,author=pica.per,subject=pica.sw,...
  ```

### DNB (Deutsche Nationalbibliothek) SRU
- **Endpoint**: `https://services.dnb.de/sru/dnb`
- **Format**: MARC21-xml
- **NL-relevantie**: matig. Goed voor Duitstalige aanvullingen.

### WorldCat (OCLC)
- **WorldCat Search API v2** (2024–2026): `https://americas.discovery.api.oclc.org/worldcat/search/v2` — vervangt v1
- **Authenticatie**: WSKey + OAuth2 client credentials. Vereist OCLC-membership of subscription voor volwaardige toegang.
- **Free tier**: WorldCat Basic API biedt 1000 queries/dag, beperkte velden (titel, auteur, ISBN/OCLC, link), output in RSS/Atom.
- **Z39.50**: `zcat.oclc.org` op poort 210, DB `OLUCWorldCat`, vereist OCLC-membership.
- **Status**: OCLC heeft sinds januari 2024 een rechtszaak lopen tegen Anna's Archive over WorldCat-data — daardoor zijn ze terughoudender met data-toegang dan vroeger.

### BnF SRU (wat je al gebruikt)
- Bevat ook Nederlandstalige werken die in Franse depots zijn opgenomen, maar dunne dekking.
- De quirks die je al kent (geen recordSchema=unimarcXchange, 200$b ≠ subtitle, dates met "DL " prefix) zijn nog steeds geldig.

### LoC (Library of Congress)
- Wat je al gebruikt op `lx2.loc.gov:210` — voor NL boeken matig, voor academische werken redelijk.

---

## 3. Generieke / commerciële boeken-API's (NL-dekking variabel)

### Open Library — wat je al gebruikt
- Werkt redelijk voor populaire NL-titels. Crowdsourced, dus kwaliteit varieert. Recente APIs:
  - Books API: `https://openlibrary.org/api/books?bibkeys=ISBN:...&format=json`
  - Covers API: `https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg`
  - Works/Editions/Authors: `https://openlibrary.org/works/OL...W.json`
- Internet Archive bezit het — politiek licht omstreden i.v.m. controlled digital lending.

### Google Books — wat je al gebruikt
- Goede dekking voor commerciële NL-titels, slechte dekking voor klein/links/akademisch.

### ISBNdb
- ~108M titels, commercieel ($). 19 datapunten per boek. Dekking NL-titels: matig.
- Rate limits: 1 req/s op gratis, 3-5 req/s op betaalde plannen.
- Voor SAF waarschijnlijk niet kosten-effectief.

### isbntools (Python framework — wat je al kent)
- Plugins voor BnF, DNB, Porbase (Portugal), LoC, **KB**, SBN (Italië) — installer met `pip install isbnlib-kb`.
- Onderhouden door @xlcnd op GitHub, recent nog updates in 2024–2025.

---

## 4. Bulk / dump-bronnen (voor offline matching of als fallback)

Deze geven geen live API, maar zijn enorme MARC21/MARCXML-dumps die je periodiek kunt downloaden en lokaal indexeren:

| Bron | Records | Format | Licentie |
|------|---------|--------|----------|
| **K10plus dump** (swblod.bsz-bw.de/od) | 87M | MARCXML | CC0 |
| **UGent (Universiteit Gent) export** | ~5M | Aleph Sequential | ODC ODbL |
| **UvA (Universiteit van Amsterdam)** | 2.7M | MARCXML | PDDL/ODC-BY |
| **KB NBT linked data dump** | miljoenen | TriG/Turtle | ODC-By |
| **Fennica (Finland nationaal)** | 1M | MARCXML | CC0 |
| **British Library** | groot | MARCXML (via Z39.50 op aanvraag) | divers |

Voor een AF-bibliotheek lijkt me een lokale K10plus-dump + de KB linked data dump samen veruit de beste fallback-strategie. Met `qa-catalogue` (github.com/pkiraly/qa-catalogue) kan je deze dumps indexeren en kwaliteitschecks doen.

---

## 5. Communities, blogs en wiki's (afgelopen ~2 jaar)

### Actief en Nederlandstalig

- **Koha Gebruikers Nederland & België** — `https://kohagebruikers.nl/`
  - Actief. Aankondiging op de homepage: **Koha gebruikersdag op 10 juni 2026 in het Rijksmuseum in Amsterdam**. Vorige editie was bij FOMU Antwerpen (juni 2025).
  - Recente posts over Koha 25.11 release (december 2025), itemtypes & collectiecodes, SQL-rapporten.
  - Voor SAF: een evenement om bij te zijn. Daar zit precies jullie peer group.

- **Cultuurconnect zendesk / nieuws** — `cultuurconnect.zendesk.com/hc/nl` en `openvlacc.cultuurconnect.be/nieuws`
  - Productgroep Open Vlacc met regelmatige posts (laatste medio 2025).
  - Bevraging Open Vlacc-werking liep oktober-november 2025.
  - Belangrijk: Aleph wordt uitgefaseerd in 2026, nieuw catalografiesysteem in marktverkenning.

- **CEMPER (Vlaanderen)** — `cemper.be/nieuws/bibliotheeksoftware-koha`
  - Uitvoerige Koha-evaluatie van september 2025 (Cultureel Erfgoed Metadata en Periodieke Erfgoedreflectie). Beschrijft ervaring van Orpheus Instituut en OPENDOEK, demobezoek, kostenstructuur. Goede sanity-check voor jullie eigen aanpak.

- **VVBAD** — `vvbad.be` (Vlaamse Vereniging voor Bibliotheek, Archief & Documentatie)
  - Gepubliceerd in 2024–2025: artikelen over openbare bibliotheken in Vlaanderen, IBL-tarieven, EBS-uitrol.

- **BiblioNext (NL)** — `biblionext.nl`
  - Commerciële Koha-hosting voor Nederland. Pitch via Z39.50, MARC/UNIMARC, koppelingen met Landelijke Digitale Infrastructuur. Niet super community-georiënteerd maar wel een referentie.

### Internationaal, regelmatig vermeld 2024–2026

- **Koha community wiki** — `wiki.koha-community.org/wiki/Configure_Z39.50/SRU_targets` — laatste edit september 2024. Lijst met servers per land.
- **KohaSupport Z39.50-directory** — `resources.kohasupport.com/z3950/` — laatste update november 2025. Live status checks van Z39.50-servers.
- **IRSpy** — `irspy.indexdata.com` — registry van Z39.50-targets, klassieker. Soms verouderd maar nuttig voor obscure bronnen.
- **z-brary.com** — directory van Z39.50/SRU targets.
- **code4lib** — `code4lib.org` — internationale community van bibliotheek-developers. Veel discussies over MARC, BibFrame, linked data.
- **OCLC Developer Network blog** — opvallend stiller sinds 2024 i.v.m. de Anna's Archive-rechtszaak.

### KB Lab (KB Research)
- **github.com/KBNLresearch** — diverse repos rond KB API's, OCR, datasets. Niet stormachtig actief maar nog onderhouden.
- **lab.kb.nl** — workshops o.a. over Frame Generator en SRU. Pagina's gedateerd 2023–2024 maar het materiaal werkt nog.

### Anna's Archive (politiek-juridisch grensgebied)
- Niet aanbevolen als productiebron, maar de **ISBN-bountyprojecten** (visualizing all ISBNs, Jan 2025) hebben publieksdomein-datasets opgeleverd die handig zijn voor offline ISBN-validatie en publisher-prefix lookups. NL ISBN-prefixen: 90-... en 94-... (Belgisch-Nederlandstalig).
- Sinds maart 2024 in NL geblokkeerd door rechter Rotterdam op verzoek BREIN. Sinds december 2024 ook UK-blok.

---

## 6. Concrete aanbevelingen voor koha-saf

### Korte termijn (geen of weinig werk)
1. **Voeg K10plus toe** aan je SRU-bronnen, na BnF. PICA-XML parsen voegt complexiteit toe, maar de dekking voor Nederlandstalige titels (vooral via UvA/UGent aanleveringen) is goed. Plak prioriteit: KB-NL → LoC → BnF → K10plus → Google → OpenLibrary.
2. **Test isbnlib-kb** als alternatief voor je eigen SRU-parser. Als de KB-NL-data identiek is maar dan met een onderhouden codebase, scheelt dat onderhoud.
3. **Vraag toegang tot Open Vlacc**-exportbestand via servicedesk@cultuurconnect.be. Vermeld jullie status als bibliotheek van een Vlaamse NGO. Een dagelijkse dump in MARC21 die je in een eigen Z39.50-faaltarget hangt of direct in je import-pipeline pluggt, zou de beste single bron voor SAF zijn.

### Middellange termijn
4. **KB SPARQL voor subject enrichment**: gebruik de Brinkman/GTT-thesaurus om jullie MARC 650 trefwoorden te verrijken met breder/nauwere termen. Dat verbetert je faceted search en speelt direct mee met je AF-categorie-systeem.
5. **Probeer de Koha-gebruikersdag van 10 juni 2026 in het Rijksmuseum**. Daar zitten precies de mensen die jouw soort vragen al hebben opgelost.

### Niet doen
- ISBNdb subscription: te duur voor de dekking die je krijgt.
- WorldCat Search API: te veel rompslomp (OAuth2 + WSKey + lidmaatschap) voor wat je terugkrijgt. De Anna's Archive-rechtszaak maakt OCLC bovendien voorzichtig met externe toegang.
- DNB SRU: dunne NL-dekking, niet de moeite waard naast K10plus.

---

## 7. Quick-reference: endpoint cheatsheet

```text
KB-NL SRU:            https://jsru.kb.nl/sru/sru?operation=searchRetrieve&x-collection=GGC&query=<ISBN>
KB-NL SPARQL:         http://data.bibliotheken.nl/sparql
K10plus SRU:          http://sru.k10plus.de/opac-de-627?version=1.1&operation=searchRetrieve&query=pica.isb=<ISBN>&recordSchema=marcxml
DNB SRU:              https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&query=dnb.num=<ISBN>&recordSchema=MARC21-xml
BnF SRU:              http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.isbn%20any%20%22<ISBN>%22
LoC Z39.50:           lx2.loc.gov:210 / LCDB (MARC21)
Open Vlacc Z39.50:    via servicedesk@cultuurconnect.be (gelicentieerd)
Meta4books REST:      via lidmaatschap (Boekenbank account)
Google Books:         https://www.googleapis.com/books/v1/volumes?q=isbn:<ISBN>
Open Library:         https://openlibrary.org/api/books?bibkeys=ISBN:<ISBN>&format=json&jscmd=data
```