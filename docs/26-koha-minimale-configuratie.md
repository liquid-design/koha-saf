# 26. Koha minimale configuratie voor SAF

**Datum:** 18 mei 2026
**Status:** studie + voorgestelde configuratie. Toepassing via wijzigingen
aan bestaande Ansible roles; geen nieuwe roles vereist.

## 26.1 Aanleiding

De Koha 25.05 installatie volgt na de Ansible playbooks 01-09 een werkende
maar generieke configuratie. Sommige defaults zijn voor onze context
(Belgische vzw-bibliotheek, één vestiging, antifascisme-collectie,
Nederlandstalige lezers) ongeschikt, onveilig of irrelevant.

Doel van deze studie: identificeren wat **minimaal** moet gebeuren om
Koha klaar te zetten voor productiegebruik door bibliothecaris en
bezoekers. Geen gold-plating, geen features die niemand gaat gebruiken —
wel een solide basis.

Buiten scope:
- Klantspecifieke catalografische conventies (MARC framework keuzes)
- ACL/permissions per gebruikersgroep (zit deels al in `koha_business_staff`)
- OPAC theming (logo, kleuren, custom CSS) — apart traject

## 26.2 Wat al goed staat

Voor we wijzigingen voorstellen, even erkennen wat al correct geconfigureerd is:

| Categorie | Locatie | Wat staat er |
|---|---|---|
| Bibliotheek-identiteit | `koha_business_libraries` | SAF-branch met naam |
| Patron-categorieën | `koha_business_patron_categories` | Medewerker, Volwassene, Jeugd |
| Item types | `koha_business_item_types` | BK actief, DVD/CD in reserve |
| Circulation rules | `koha_business_circulation` | 14 dagen, 2 verlengingen |
| Basis sysprefs | `koha_business_sysprefs` | URLs, taal, naam, MARC21 |
| Admin account | `koha_business_admin` | kohaadmin met superlibrarian |

Dit dekt de Koha-basis. Wat ontbreekt zijn de "operationele" zaken:
e-mail kunnen sturen, gepaste lezersfeedback, juiste tijdzone, privacy-defaults
voor een EU-context, en cover-verrijking voor de OPAC.

## 26.3 Gap-analyse per Koha-tab

Op `https://bib-test-intra.marxisme.be/cgi-bin/koha/admin/preferences.pl`
staan 20 tabs met systeempreferences. Hieronder per tab wat voor SAF
relevant is en wat niet.

### 26.3.1 Hoge prioriteit (moet)

**Administration** — SMTP server, tijdzone, e-mailadressen
**OPAC** — adres dat lezers zien, privacy policy, taal
**Patrons** — wachtwoord-policy, zelfregistratie aan/uit
**I18N/L10N** — datum/tijd formaat (DD/MM/YYYY voor BE)
**Enhanced content** — `OpenLibraryCovers` (gratis verrijking)
**Logs** — actie-logging voor traceerbaarheid

### 26.3.2 Middelhoge prioriteit (zou)

**Circulation** — kleine fine-tuning op overdues, holds
**Cataloging** — autoBarcode-format, default frameworks
**Authorities** — autoCreateAuthorities aan zodat namen meegroeien met catalogus
**Searching** — zoekgedrag voor Nederlandstalige catalogus

### 26.3.3 Lage of geen prioriteit (kan / niet)

| Tab | Status | Reden |
|---|---|---|
| Accounting | Niet | SAF rekent geen boetes aan |
| Acquisitions | Niet | Aanwinsten lopen niet via Koha order-flow |
| E-resource management | Niet | Geen digitale collectie |
| Interlibrary loans | Niet voor 2026 | Mogelijk later, na Open Vlacc-traject |
| Preservation | Niet | Geen archivering-workflow |
| Serials | Niet | Geen tijdschriften in collectie |
| Web services | Niet | Geen integraties van derden |

## 26.4 Voorgestelde configuratie

Hieronder per onderdeel: wat zetten, naar welke waarde, en waarom.

### 26.4.1 SMTP — e-mail uit Koha kunnen sturen

Zonder SMTP kan Koha geen wachtwoord-reset doen, geen herinneringen
voor te late items, geen reserveringsmeldingen. Met de mail-infrastructuur
op `mail.socialisme.be` en de bestaande mailboxen kunnen we dit direct
configureren.

Koha 25.05 ondersteunt SMTP-servers als objecten in een aparte
admin-pagina (`/cgi-bin/koha/admin/smtp_servers.pl`), niet als sysprefs.
Dit vereist een eigen Ansible-task die via SQL een rij invoegt in de
`smtp_servers` tabel en die als default markeert.

**Configuratie (per omgeving via group_vars):**

```yaml
# group_vars/test.yml
koha_smtp_host: mail.socialisme.be
koha_smtp_port: 587
koha_smtp_user: saf-test@marxisme.be
koha_smtp_pass: "{{ vault_koha_smtp_pass }}"   # in ansible-vault
koha_smtp_tls: starttls
koha_email_from: saf-test@marxisme.be
koha_email_reply_to: saf-test@marxisme.be
```

```yaml
# group_vars/prod.yml
koha_smtp_host: mail.socialisme.be
koha_smtp_port: 587
koha_smtp_user: saf@marxisme.be
koha_smtp_pass: "{{ vault_koha_smtp_pass_prod }}"
koha_smtp_tls: starttls
koha_email_from: saf@marxisme.be
koha_email_reply_to: saf@marxisme.be
```

**Gekoppelde sysprefs:**

```yaml
- pref: KohaAdminEmailAddress
  value: "{{ koha_email_from }}"

- pref: ReplytoDefault
  value: "{{ koha_email_reply_to }}"

- pref: SendAllEmailsTo
  value: ""  # leeg = normaal versturen. Op test eventueel "sander@..."
             # zetten om alle mail te onderscheppen tijdens proefdraaien.
```

**Veiligheidsoverweging**: SMTP-wachtwoorden komen in
`inventory/group_vars/all/vault.yml` (ansible-vault, niet plaintext).
De vault-password file zelf staat in `.gitignore`.

### 26.4.2 Lokalisatie — datum/tijd in Vlaams formaat

Standaard toont Koha datums in YYYY-MM-DD. Vlaamse bibliothecaris
verwacht DD/MM/YYYY. Tijdzone op `Europe/Brussels` zodat overdue-berekeningen
kloppen rondom middernacht.

```yaml
- pref: dateformat
  value: "dmydot"   # 18.05.2026 — meest gangbare BE notatie
                    # Alternatief: "metric" → 18/05/2026

- pref: timeformat
  value: "24hr"     # 14:30 ipv 2:30 PM

- pref: TimeFormat
  value: "24hr"     # nieuwere preference, zelfde functie

- pref: CalendarFirstDayOfWeek
  value: "1"        # 1 = maandag (Vlaamse conventie)
```

Tijdzone wordt OS-level in koha-conf gezet, niet via syspref. Check:

```bash
sudo cat /etc/koha/sites/{{ koha_instance }}/koha-conf.xml | grep -i timezone
```

Zou `Europe/Brussels` moeten zijn. Als niet, aan te passen in
`koha_instance` role.

### 26.4.3 OPAC — wat de bezoeker ziet

```yaml
# Welkomsttekst is al gezet via OpacMainUserBlock — behouden

# Bezoekers mogen zoeken zonder inloggen (al gezet via OpacPublic=1)
# Bezoekers kunnen niet zelf account aanmaken
- pref: PatronSelfRegistration
  value: "0"        # SAF bepaalt zelf wie lid wordt, geen self-service

# Verbergen wat we niet hebben
- pref: OPACShowCheckoutName
  value: "0"        # privacy: niet tonen wie iets uitleende

# Lezers kunnen hun eigen leengeschiedenis NIET zien (privacy default)
# Zit al in StoreLastBorrower=0 — behouden

# Privacy policy verplicht onder GDPR
- pref: PrivacyPolicyURL
  value: "https://marxisme.be/privacy"  # of waar jullie hem hosten
- pref: PrivacyPolicyConsent
  value: "1"
```

### 26.4.4 Patron-security — wachtwoorden niet zwak

```yaml
# Minimum lengte: 8 tekens (Koha default is 3, te zwak)
- pref: minPasswordLength
  value: "8"

# Wachtwoord moet sterk zijn (cijfer + hoofdletter)
- pref: RequireStrongPassword
  value: "1"

# Patron logs bijhouden: ja, voor audit
# (voor SAF beperkt nuttig — kleine ledenkring — maar geen kost)
```

### 26.4.5 Enhanced content — Open Library covers

Zoals besproken in eerdere chat:

```yaml
- pref: OpenLibraryCovers
  value: "1"        # Show. Cover dekking ~20% voor SAF-collectie,
                    # gratis, geen API key nodig.

# Andere cover-bronnen UIT laten — conflict
- pref: GoogleJackets
  value: "0"
- pref: AmazonCoverImages
  value: "0"
- pref: OPACAmazonCoverImages
  value: "0"
```

### 26.4.6 Cataloging — kleine quality-of-life

```yaml
# autoBarcode incrementeel staat al goed — behouden

# Standaard MARC framework: leeg = default. Voor BK gebruiken we
# de default. Geen wijziging nodig nu.

# Autoriteiten automatisch aanmaken bij eerste gebruik van een naam
# Voorkomt handmatig elk auteursnaamveld te koppelen
- pref: AutoCreateAuthorities
  value: "1"

# Bij nieuwe ISBN duplicate-detectie tonen aan catalografische gebruiker
# (sluit aan bij eerdere "match found, ignored" discussie)
- pref: AggressiveMatchOnISBN
  value: "1"
```

### 26.4.7 Logs — voor traceerbaarheid

```yaml
# Wie wat catalogiseerde, wanneer
- pref: CataloguingLog
  value: "1"

# Wie loggde in en wanneer
- pref: AuthSuccessLog
  value: "1"
- pref: AuthFailureLog
  value: "1"

# Lidmaatschap-wijzigingen
- pref: BorrowersLog
  value: "1"

# Uitleen-events
- pref: IssueLog
  value: "1"
- pref: ReturnLog
  value: "1"
```

Logs blijven 90 dagen staan, dan cleanup via Koha cron-task die al
draait. Geen extra schijfgebruik om je zorgen over te maken.

### 26.4.8 Searching — Nederlandstalige defaults

```yaml
# Bij zoeken in OPAC: stem-search aan voor NL
# (zoekt "geschiedenis" en vindt ook "geschiedenissen")
- pref: UseICUStyleQuotes
  value: "1"

# Maximum aantal zoekresultaten op één pagina
- pref: OPACnumSearchResults
  value: "20"

# Aantal resultaten in staff client
- pref: numSearchResults
  value: "20"
```

## 26.5 Smoke test na deploy

Eens alles gedeployed: minimale checklist om te verifiëren dat
configuratie werkt.

1. **SMTP test**: bib-test-intra → Tools → Notices and slips → klik
   "Test email" knop. Mail moet aankomen op `saf-test@marxisme.be`.

2. **Datum**: ergens in staff client (bv. patron-detail) staat een datum
   in DD/MM/YYYY of DD.MM.YYYY formaat.

3. **OPAC privacy**: bezoek `https://bib-test.marxisme.be`, scrol naar
   onder, link naar privacybeleid zichtbaar.

4. **OpenLibraryCovers**: zoek in OPAC naar ISBN 9780140445695 (Capital,
   Penguin). Cover moet zichtbaar zijn naast de zoekresultaat.

5. **Wachtwoord-policy**: probeer een patron aan te maken met wachtwoord
   "123". Moet weigeren met melding "minimum 8 tekens".

6. **Log-flow**: log in als kohaadmin → Tools → Log viewer → check
   dat je eigen login is geregistreerd.

## 26.6 Waar wat staat in Ansible

Voor toekomstige aanpassingen — bekijk eerst onderstaande tabel voor de
juiste plek. Niet alles in één bestand zetten, dit hoort verspreid.

| Wijziging | Bestand |
|---|---|
| Sysprefs algemeen | `roles/koha_business_sysprefs/defaults/main.yml` |
| Per-omgeving sysprefs override | `inventory/group_vars/{test,prod}.yml` |
| SMTP credentials | `inventory/group_vars/all/vault.yml` (encrypted) |
| SMTP server task | `roles/koha_business_smtp/tasks/main.yml` (nieuw) |
| Tijdzone | `roles/koha_instance/tasks/main.yml` |
| Patron categorieën | `roles/koha_business_patron_categories/defaults/main.yml` |
| Item types | `roles/koha_business_item_types/defaults/main.yml` |
| Circulation rules | `roles/koha_business_circulation/defaults/main.yml` |
| Authorised values | `roles/koha_business_authorised_values/defaults/main.yml` |

### Wijzigingsworkflow

```bash
# 1. Branch maken
git checkout -b feature/koha-business-config

# 2. Aanpassing maken in juiste bestand
$EDITOR roles/koha_business_sysprefs/defaults/main.yml

# 3. Deployen op test
ansible-playbook -i inventory/terraform.py -l test playbooks/07-koha-business.yml

# 4. Verifiëren in https://bib-test-intra.marxisme.be

# 5. Bij succes: commit + merge naar main + deploy prod
git add ...
git commit -m "..."
git checkout main && git merge feature/koha-business-config
ansible-playbook -i inventory/terraform.py -l prod playbooks/07-koha-business.yml
```

### Waarde van een syspref opzoeken zonder UI

Soms wil je weten wat een preference nu is zonder via de browser. Direct
in MySQL:

```bash
ssh bib-test
sudo koha-mysql bib <<EOF
SELECT variable, value FROM systempreferences
WHERE variable IN (
  'OpenLibraryCovers', 'KohaAdminEmailAddress',
  'PatronSelfRegistration', 'minPasswordLength'
);
EOF
```

Handig om te checken of een Ansible-run de waarde echt gezet heeft.

## 26.7 Wat we bewust NIET doen

Belangrijk om vast te leggen, anders worden deze in een toekomstige
review weer ter sprake gebracht:

- **Geen self-service registration** (`PatronSelfRegistration=0`):
  SAF bepaalt wie lid wordt, geen open inschrijvingen vanuit OPAC.
- **Geen externe authenticatie** (LDAP/SSO/CAS): kleine ledenkring,
  geen waarde tegenover de operationele complexiteit.
- **Geen Acquisitions module**: aanwinsten lopen via de Flask
  ISBN-import (`scan.marxisme.be`), niet via Koha order-management.
- **Geen Syndetics/LibraryThing/NoveList**: commerciële services,
  geen budget voor, geen toegevoegde waarde voor de SAF-collectieprofiel.
- **Geen Z39.50/SRU servers als external targets**: Koha kan zelf
  externe catalogi bevragen (`/cgi-bin/koha/admin/z3950servers.pl`)
  maar de Flask-app doet dit beter voor onze flow. Niet inschakelen
  om verwarring te voorkomen tussen "Flask haalt iets op" en "Koha
  haalt iets op".

## 26.8 Vervolg

Na implementatie van deze studie:

1. **Notice templates aanpassen** — Koha levert generieke Engelse
   templates voor "Item due in 3 days" e.d. Voor Vlaamse lezers herschrijven
   naar Nederlandse versies. Wachten tot er een paar uitleningen geweest
   zijn in test, dan op basis van echte uitstuur-content beoordelen.

2. **Notice cronjobs activeren** — `koha-foreach --enabled "advance_notices.pl"`
   etc. Moet via `koha-finalize` of `koha_business_circulation` toegevoegd
   worden.

3. **Open Vlacc integratie** — afhankelijk van Cultuurconnect-antwoord
   (zie doc 24). Geen vervolg op deze doc voor SAF nodig, los traject.

4. **Backup-role landen** — doc 20-23 over de B2-backupstrategie
   afmaken en deployen.
