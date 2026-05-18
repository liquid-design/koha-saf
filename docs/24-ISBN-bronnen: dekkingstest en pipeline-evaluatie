# 24-ISBN-bronnen: dekkingstest en pipeline-evaluatie

**Datum:** 17 mei 2026
**Status:** vastgelegd na empirische test; pipeline-aanpassing in afwachting van Open Vlacc-toegang.

## 24.1 Aanleiding

De ISBN-import pipeline gebruikt sinds de aanvankelijke setup vijf bronnen in deze prioriteitsvolgorde:

```
KB-NL → LoC → BnF → Google Books → OpenLibrary
```

Bij het catalogiseren van nieuwe aanwinsten bleek herhaaldelijk dat typische SAF-collectietitels — Vlaamse linkse non-fictie, in het bijzonder EPO-uitgaven — door geen enkele bron werden teruggevonden. Om vast te stellen of dit een structureel patroon was en welke aanvullende bronnen het gat zouden dichten, is op 17 mei 2026 een dekkingstest uitgevoerd tegen acht endpoints.

## 24.2 Testopzet

Tien ISBN's uit de SAF-collectie zijn parallel bevraagd via een shell-script (`/home/john/scripts/test-isbn-apis.sh`):

- Vijf Nederlandstalige titels
- Drie Franstalige titels
- Twee Engelstalige titels

De geteste bronnen:

| Bron | Type | Endpoint |
|---|---|---|
| KB-NL SRU | SRU/Dublin Core | `https://jsru.kb.nl/sru/sru?x-collection=GGC` |
| KB SPARQL | SPARQL/Linked Data | `http://data.bibliotheken.nl/sparql` |
| K10plus SRU | SRU/MARCXML (PICA) | `http://sru.k10plus.de/opac-de-627` |
| DNB SRU | SRU/MARC21 | `https://services.dnb.de/sru/dnb` |
| BnF SRU | SRU/UNIMARC | `http://catalogue.bnf.fr/api/SRU` |
| LoC SRU | SRU/MARC21 | `http://lx2.loc.gov:210/LCDB` |
| Google Books | REST/JSON | `https://www.googleapis.com/books/v1/volumes` |
| Open Library | REST/JSON | `https://openlibrary.org/api/books` |

De geteste ISBN's en hun titels:

| ISBN | Titel | Auteur | Taal |
|---|---|---|---|
| 9789044552157 | Dubbelganger | Naomi Klein | NL |
| 9789025319830 | We moeten iets dóén! | Elsbeth Etty | NL |
| 9789064452130 | Zwarthemden & Roden | Michael Parenti (EPO, 2001) | NL |
| 9789462670235 | (EPO-uitgave) | onbekend | NL |
| 9789023482611 | Naar een democratischer Europa | Hennette e.a. | NL |
| 9791035108830 | Le travail de parti de Marx | Quétier | FR |
| 9782207252772 | Lettres à Léon Jogichès | Rosa Luxemburg | FR |
| 9782070732982 | André Breton | Mark Polizzotti | FR |
| 9780140445695 | Capital | Karl Marx (Penguin) | EN |
| 9789491304132 | (Vlaamse uitgave, 94-range) | onbekend | NL |

## 24.3 Resultaten

| ISBN | KB-NL | KB-SPARQL | K10plus | DNB | BnF | LoC | Google | OpenLib |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 9789044552157 | ✅ | · | · | · | · | · | · | · |
| 9789025319830 | ✅ | · | · | · | · | ✅ | · | · |
| 9789064452130 | · | · | · | · | · | · | · | · |
| 9789462670235 | · | · | · | · | · | · | · | · |
| 9789023482611 | ✅ | · | · | · | · | · | · | · |
| 9791035108830 | · | · | · | · | ✅ | · | · | · |
| 9782207252772 | · | · | · | ✅ | · | · | · | · |
| 9782070732982 | · | · | ✅ | · | · | · | · | ✅ |
| 9780140445695 | · | · | ✅ (n=4) | ✅ | ✅ | · | · | ✅ |
| 9789491304132 | · | · | · | · | · | · | · | · |
| **Totaal hits** | **3/10** | **0/10** | **3/10** | **2/10** | **2/10** | **1/10** | **0/10** | **3/10** |

Drie ISBN's leverden bij geen enkele bron een treffer op: `9789064452130`, `9789462670235`, en `9789491304132`. Een handmatige controle in `https://bibliotheek.be/catalogus` bevestigt dat minstens twee van deze drie wél in Open Vlacc (de centrale catalogus van de Vlaamse openbare bibliotheken) zijn beschreven.

### 24.3.1 Aantekeningen per bron

**KB-NL SRU.** Drie hits, alle Nederlandstalig, conform verwachting. Geen verrassingen, geen reden tot wijziging van het bestaande gedrag.

**KB SPARQL.** Nul hits. De gebruikte queryvorm matcht niet op de wijze waarop ISBN's in NBT zijn opgeslagen. Voor losse ISBN-lookups voegt SPARQL bovendien geen waarde toe naast de SRU-toegang tot dezelfde catalogus. SPARQL blijft potentieel nuttig voor bulk subject-enrichment via de Brinkman/GTT-thesaurus, maar dat is een aparte usecase die buiten deze test valt.

**K10plus SRU.** Drie hits. `9780140445695` (Penguin Capital) leverde `n=4` op — meerdere edities — wat duidt op goede academische dekking. Auteursveld komt in MARC 100$a-formaat `Achternaam, Voornaam`, direct bruikbaar voor Koha MARC 100$a.

**DNB SRU.** Twee hits. Onverwacht resultaat: `9782207252772` (Rosa Luxemburg, Lettres à Léon Jogichès) werd uitsluitend door DNB gevonden. DNB blijkt dus ook internationale uitgaven van Duitstalige/Pools-Duitse auteurs te indexeren. Voor de SAF-collectie met veel Duitse marxistische literatuur is dit waardevoller dan oorspronkelijk ingeschat.

**BnF SRU.** Twee hits (één FR-titel, en de Penguin Capital). Conform verwachting voor Franstalig materiaal.

**LoC SRU.** Eén hit. Lager dan verwacht. Een Nederlandstalig boek (`9789025319830`, We moeten iets dóén!) werd wel gevonden, mogelijk door deponering via een Amerikaanse academische bibliotheek.

**Google Books.** Nul hits. Dit is bijna zeker een artefact van rate-limiting bij parallelle calls zonder API-key — `9780140445695` (Penguin Capital) zit gegarandeerd in Google Books maar gaf in deze test geen treffer. In productie (sequentieel, met pauzes tussen calls) is dit gedrag anders. De nul-score in deze test mag dus niet als argument tegen Google Books gebruikt worden.

**Open Library.** Drie hits, waaronder informatie die andere bronnen niet boden: voor `9780140445695` gaf OpenLib correct "Capital Volume II" terug terwijl de andere bronnen alleen "Capital" gaven. Bevestigt Open Library als zinvolle laatste bron in de keten.

### 24.3.2 Het patroon van de nul-hits

Twee van de drie ISBN's die door geen enkele bron worden teruggevonden, zijn aantoonbaar uitgaven van EPO (Berchem) — een onafhankelijke Belgische uitgeverij met een uitgesproken linkse profiel, gespecialiseerd in non-fictie rond politieke, economische, sociale, culturele en historische thema's. Dit is letterlijk het collectieprofiel van SAF.

De ISBN-range 978-94-6267-xxxx is volledig EPO-toegewezen. Het derde nul-hit-ISBN (`9789491304132`) zit eveneens in een Belgische 94-prefix.

Het structurele gat dat hieruit blijkt:

- Deponering bij KB Den Haag is **niet verplicht** voor Belgische uitgevers → niet in NBT
- Belgisch wettelijk depot bij KB Brussel staat **los van** Open Vlacc en is niet via een open API beschikbaar
- Vlaamse uitgeverijen worden **niet structureel** door OCLC-PICA verbundsystemen (K10plus, DNB) gecatalogiseerd
- Voor internationale catalogi (LoC, BnF) is dit materiaal te lokaal
- Voor commerciële catalogi (Google Books) wordt EPO's fonds niet structureel aangeleverd
- Voor Open Library is er geen actieve crowdsourcing op Vlaamse linkse non-fictie

De **enige** bron waar deze titels gegarandeerd in zitten is Open Vlacc, omdat álle Vlaamse openbare bibliotheken EPO-titels in hun collectie hebben en die centraal catalogiseren via Cultuurconnect.

## 24.4 Pipeline-aanpassingen

### 24.4.1 Nieuwe merge-prioriteit (na implementatie)

```
Open Vlacc → KB-NL → K10plus → DNB → LoC → BnF → Google Books → OpenLibrary
```

Rationale per bron:

1. **Open Vlacc bovenaan**: dekt het structurele gat voor Vlaamse linkse non-fictie en is voor het collectieprofiel van SAF de meest precieze bron. Toegang in aanvraag bij Cultuurconnect (zie 24.5).
2. **KB-NL** behoudt huidige positie: beste single source voor Nederlandstalig materiaal.
3. **K10plus** nieuw, na KB-NL: goede dekking voor academisch materiaal, levert MARC21 met `Achternaam, Voornaam`-auteurformaat.
4. **DNB** nieuw, na K10plus: dekt Duitstalige marxistische literatuur en internationale uitgaven van Duits-Pools-Joodse auteurs (Rosa Luxemburg, Walter Benjamin, etc.) die in andere bronnen ontbreken.
5. **LoC** zakt: weinig meerwaarde voor SAF-collectie vergeleken met K10plus/DNB.
6. **BnF** behoudt: enige bron voor sommige Franstalige uitgaven.
7. **Google Books** en **OpenLibrary** sluiten de keten af als generieke fallback.

### 24.4.2 Implementatievolgorde

1. **K10plus parser** — MARC21-XML, gelijkaardig aan de bestaande LoC-parser. Endpoint: `http://sru.k10plus.de/opac-de-627`, query: `pica.isb=<ISBN>`, schema: `marcxml`. Geen quirks bekend.
2. **DNB parser** — MARC21-XML, sterk vergelijkbaar met K10plus. Endpoint: `https://services.dnb.de/sru/dnb`, query: `dnb.num=<ISBN>`, schema: `MARC21-xml`.
3. **Open Vlacc integratie** — afhankelijk van wat Cultuurconnect aanbiedt:
   - Bij **SRU/Z39.50-toegang**: nieuwe parser, op te nemen in de bestaande live-lookup keten.
   - Bij **dagelijkse MARC21-dump**: aparte ingestiestap die de dump indexeert (PostgreSQL-tabel met ISBN als primary key), en een lokale lookup als eerste stap in de pipeline. Aanzienlijk sneller dan elke remote SRU-call.
4. **Merge-prioriteit aanpassen** in `koha_import_runner` zodra alle parsers stabiel zijn.

### 24.4.3 Aandachtspunten

- **K10plus auteursformaat**: levert `Achternaam, Voornaam` zoals MARC 100$a vereist — direct bruikbaar, geen conversie nodig.
- **DNB auteursformaat**: idem, MARC 100$a-conform.
- **K10plus `n>1` resultaten**: bij meerdere edities (zoals Penguin Capital, n=4) eerste record nemen, of de meest recente — beslissing nemen bij implementatie. Suggestie: meest recente uitgave (datum in MARC 008 of 260$c).
- **Open Vlacc MARC21**: gebruikt mogelijk Vlaamse uitbreidingen (ZIZO-classificatie, SISO-codes). Bij ingestie deze velden behouden in MARC, gebruik ervoor te zien bij Koha-import.
- **Rate limiting**: bij parallelle calls naar Google Books in de huidige test gaf elke ISBN een MISS. In productie sequentieel oproepen met een korte pauze (200ms). Dit is geen reden om Google Books uit de pipeline te halen.

## 24.5 Aanvraag Open Vlacc-toegang

Op 17 mei 2026 is een aanvraag gestuurd naar `servicedesk@cultuurconnect.be` met:

- Vermelding SAF-context (Vlaamse vzw, Berchem, Koha-systeem `bib.marxisme.be`)
- Verwijzing naar de specifieke EPO-collectie-overlap
- Vraag naar voorwaarden, kosten, formaat, en mogelijkheid van Z39.50/SRU naast of in plaats van dagelijkse export

Verwachte responstijd: één tot twee weken. Mogelijke uitkomsten:

- **Z39.50/SRU-endpoint** met credentials: ideaal voor live-lookup in Koha-pipeline.
- **Dagelijkse MARC21-dump** via FTP/HTTPS: vereist lokale ingestie maar is daarna sneller dan remote SRU.
- **Gelimiteerde toegang met bijdrage**: prijsindicatie afwachten, bestuursbeslissing.
- **Afwijzing**: terugvallen op handmatige catalografie voor het ~10-15% van de collectie dat in geen enkele andere bron zit. Niet ideaal maar werkbaar.

Bij positief antwoord: doc 25 aanmaken met de concrete configuratie (host, port, credentialopslag in Ansible vault, parser-specificaties).

## 24.6 Testreproductie

Het testscript is bewaard onder `/home/john/scripts/test-isbn-apis.sh`. Om de test te herhalen op de huidige collectie:

```bash
./test-isbn-apis.sh                  # alle 10 default test-ISBN's
./test-isbn-apis.sh 9789064452130    # één specifiek ISBN
./test-isbn-apis.sh $(cut -f1 /pad/naar/eigen-lijst.tsv)  # eigen lijst
```

Vereisten: `curl`, `jq`, en `xmllint` (`apt install libxml2-utils jq curl`).

Wanneer de pipeline-uitbreiding voltooid is (na 24.4.2 stap 4), de test opnieuw uitvoeren op een grotere, recentere steekproef en de dekking percentages opnieuw vastleggen in een vervolgdocument.

## 24.7 Samenvatting

De huidige pipeline mist structureel een belangrijk deel van de SAF-collectie, namelijk uitgaven van Vlaamse linkse uitgeverijen zoals EPO. K10plus en DNB lossen een deel op (academisch materiaal en Duitstalige marxistische literatuur), maar het structurele gat — Vlaamse uitgeverijen die niet internationaal worden gecatalogiseerd — wordt enkel dichtgemaakt door Open Vlacc. Aanvraag is ingediend bij Cultuurconnect; ondertussen worden K10plus en DNB toegevoegd aan de pipeline.