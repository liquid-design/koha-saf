# 14. OPAC system preferences (lezer-gedrag)

Dit document geeft een overzicht van de Koha system preferences die bepalen wat een lezer kan doen op de OPAC, en aanbevolen instellingen voor de SAF-context.

> **Pad in Koha:** `Administration > System preferences > OPAC` (er staan ook relevante prefs onder `Patrons` en `Circulation`).

---

## 14.1 Overzicht van de domeinen

Het lezer-gedrag wordt door een tiental sysprefs samen bepaald, gegroepeerd in vier domeinen:

| Domein                        | Waar in Koha                              | Bepaalt o.a.                        |
| ----------------------------- | ----------------------------------------- | ----------------------------------- |
| **Toegang & login**           | OPAC + Authentication                     | Wie mag de OPAC zien? Self-register?|
| **Account & gegevens**        | OPAC + Patrons                            | Wat mag lezer zelf wijzigen?        |
| **Catalogus & zoeken**        | OPAC + Searching                          | Hoe ziet de zoekervaring eruit?     |
| **Acties (hold, renew, etc.)**| OPAC + Circulation                        | Mag lezer zelf reserveren/verlengen?|

---

## 14.2 Toegang & login

### `OpacPublic`
- **Wat:** moet een lezer ingelogd zijn om de catalogus te zien?
- **Waarden:** `Allow not logged in users to view OPAC` / `Don't allow`.
- **Aanbeveling SAF:** `Allow` — laagdrempelige catalogus.

### `PatronSelfRegistration`
- **Wat:** mogen leners zichzelf registreren via de OPAC?
- **Aanbeveling SAF:** `Disable` — staff doet inschrijvingen aan de balie. Voorkomt spam-accounts.

### `OpacResetPassword`
- **Wat:** mag een lezer wachtwoord opnieuw instellen via "wachtwoord vergeten"-flow?
- **Aanbeveling SAF:** `Allow`, mits e-mailverzending betrouwbaar werkt. Anders `Don't allow` en laat staff resets doen.
- **Vereist:** `KohaAdminEmailAddress` ingesteld + werkende e-mailverzending.

### `FailedLoginAttempts`
- **Wat:** na hoeveel mislukte logins wordt een account tijdelijk geblokkeerd?
- **Aanbeveling SAF:** `5`. Beschermt tegen brute-force.

### `OpacPasswordChange`
- **Wat:** mag een ingelogde lezer zijn wachtwoord wijzigen?
- **Aanbeveling SAF:** `Allow`.

### `minPasswordLength` en `RequireStrongPassword`
- **Aanbeveling SAF:** `minPasswordLength: 8`, `RequireStrongPassword: Require` (minstens 1 hoofdletter, 1 kleine letter, 1 cijfer).

---

## 14.3 Account & gegevens

### `OPACPatronDetails`
- **Wat:** mag lezer eigen gegevens (adres, telefoon) wijzigen via OPAC?
- **Aanbeveling SAF:** `Allow` — wijzigingen gaan dan eerst naar staff voor goedkeuring.

### `OpacRenewalAllowed`
- **Wat:** mag lezer eigen leningen verlengen via OPAC?
- **Aanbeveling SAF:** `Allow`. De circulatieregels (max renewals + no-renewal-before) bepalen alsnog of het slaagt.

### `OpacRenewalBranch`
- **Wat:** welke branchcode wordt gebruikt voor statistieken bij OPAC-renewals?
- **Aanbeveling SAF:** `the patron's home branch` — meest logisch met één vestiging.

### `OPACPrivacy`
- **Wat:** mag lezer kiezen of zijn leesgeschiedenis bewaard wordt?
- **Aanbeveling SAF:** `Allow` — privacy-respect.

### `opacreadinghistory`
- **Wat:** wordt leesgeschiedenis sowieso bijgehouden?
- **Aanbeveling SAF:** `Allow` (in combinatie met `OPACPrivacy` heeft de lezer zelf controle).

### `OpacAllowSharingPrivateLists`
- **Wat:** mogen lezers hun privé-boekenplanken delen?
- **Aanbeveling SAF:** `Allow`.

### `AnonSuggestions`
- **Wat:** mogen niet-ingelogde gebruikers aankoopsuggesties indienen?
- **Aanbeveling SAF:** `Don't allow`.

---

## 14.4 Catalogus & zoeken

### `OpacKohaUrl`
- **Wat:** moet er een "Powered by Koha"-link onderaan staan?
- **Aanbeveling SAF:** `Don't show` (cosmetisch).

### `OPACdidyoumean`
- **Wat:** "Did you mean ..."-suggesties bij geen resultaten.
- **Aanbeveling SAF:** `Allow`.

### `OpacAddMastheadLibraryPulldown`
- **Wat:** dropdown bovenaan om te filteren op vestiging.
- **Aanbeveling SAF:** `Don't show` (slechts één vestiging). Aanzetten zodra meerdere vestigingen actief zijn.

### `SearchEngine`
- **Aanbeveling SAF:** `Zebra` — eenvoudiger te beheren, voldoende voor kleine collectie.

### `OPACShowHoldQueueDetails`
- **Wat:** ziet lezer hoeveel andere reserveringen er voor hem in de wachtrij staan?
- **Aanbeveling SAF:** `Show priority` — geeft transparantie zonder andere lezers te tonen.

### `BiblioDefaultView`
- **Aanbeveling SAF:** `normal` — gebruiksvriendelijk.

---

## 14.5 Acties: holds, renewals, suspensions

### `OPACHoldRequests`
- **Wat:** mag lezer reserveringen plaatsen via OPAC?
- **Aanbeveling SAF:** `Allow`.

### `OPACAllowUserToChooseBranch`
- **Wat:** mag lezer pickup branch kiezen bij hold?
- **Aanbeveling SAF:** `Allow` — relevant zodra meer vestigingen.

### `OPACAllowHoldDateInFuture`
- **Wat:** mag lezer een hold plaatsen die pas in de toekomst actief wordt?
- **Aanbeveling SAF:** `Don't allow` om te beginnen — eenvoud.

### `OpacHoldNotes`
- **Aanbeveling SAF:** `Allow`.

### `SuspendHoldsOpac`
- **Wat:** mag lezer eigen reserveringen tijdelijk pauzeren (vakantie)?
- **Aanbeveling SAF:** `Allow`.

### `AutoResumeSuspendedHolds`
- **Wat:** worden gepauzeerde reserveringen automatisch hervat op de geplande datum?
- **Aanbeveling SAF:** `Allow`.

### `canreservefromotherbranches`
- **Wat:** mag een lezer een hold plaatsen op een item dat in een andere branch staat?
- **Aanbeveling SAF:** `Allow` — vooruitkijkend naar multi-vestiging.

### `OPACFineNoRenewalsBlockAutoRenew`
- **Wat:** als een lezer boete heeft die boven de drempel uitkomt, mogen auto-renewals dan stoppen?
- **Aanbeveling SAF:** `Block` (default).

---

## 14.6 Notices & e-mailcommunicatie

Dit zit niet onder OPAC sysprefs maar onder `Patrons` / `Circulation`, en bepaalt wat de lezer ziet/krijgt.

### `EnhancedMessagingPreferences`
- **Wat:** mogen lezers zelf bepalen welke notices ze ontvangen?
- **Aanbeveling SAF:** `Allow`.

### `EnhancedMessagingPreferencesOPAC`
- **Wat:** mogen lezers deze voorkeuren via OPAC instellen?
- **Aanbeveling SAF:** `Show`.

### `KohaAdminEmailAddress`
- **Wat:** afzender-adres voor systeem-mails. **Verplicht** voor werkende e-mail.
- **Aanbeveling SAF:** `bib@marxisme.be` of vergelijkbaar.

### `AutoEmailNewUser`
- **Wat:** verstuur welkom-e-mail bij inschrijving?
- **Aanbeveling SAF:** `Send`.

### `OverdueNoticeFrom`
- **Aanbeveling SAF:** `branch email`.

---

## 14.7 Branding & uitstraling

### `opacuserlogin`
- **Aanbeveling SAF:** `Show`.

### `OpacMainUserBlock`
- **Wat:** HTML voor het centrale tekstblok op de OPAC homepage.
- **Aanbeveling SAF:** kort welkomstbericht + link naar bibliotheekinformatie. Configureerbaar via `Tools > HTML customizations` (sinds 25.05).

### `OpacNav` en `OpacNavBottom`
- **Wat:** navigatie-links links op OPAC, en onderaan.
- **Aanbeveling SAF:** vul aan met links naar website, openingsuren, contactinformatie.

---

## 14.8 Aanbevolen samenvatting voor SAF (snel-instellijst)

Voor een snelle eerste run; voor productie alles individueel verifiëren.

| Preference                          | Waarde                          |
| ----------------------------------- | ------------------------------- |
| `OpacPublic`                        | Allow                           |
| `PatronSelfRegistration`            | Disable                         |
| `OpacResetPassword`                 | Allow (mits mail werkt)         |
| `FailedLoginAttempts`               | 5                               |
| `OpacPasswordChange`                | Allow                           |
| `minPasswordLength`                 | 8                               |
| `RequireStrongPassword`             | Require                         |
| `OPACPatronDetails`                 | Allow (met goedkeuring staff)   |
| `OpacRenewalAllowed`                | Allow                           |
| `OPACPrivacy`                       | Allow                           |
| `opacreadinghistory`                | Allow                           |
| `OPACHoldRequests`                  | Allow                           |
| `OPACAllowUserToChooseBranch`       | Allow                           |
| `OPACAllowHoldDateInFuture`         | Don't allow                     |
| `OpacHoldNotes`                     | Allow                           |
| `SuspendHoldsOpac`                  | Allow                           |
| `AutoResumeSuspendedHolds`          | Allow                           |
| `OPACShowHoldQueueDetails`          | Show priority                   |
| `EnhancedMessagingPreferences`      | Allow                           |
| `EnhancedMessagingPreferencesOPAC`  | Show                            |
| `AutoEmailNewUser`                  | Send                            |
| `KohaAdminEmailAddress`             | bib@marxisme.be                 |
| `OPACdidyoumean`                    | Allow                           |
| `BiblioDefaultView`                 | normal                          |

---

## 14.9 Configuratie via Ansible

System preferences worden in dit project gezet via de role `koha_business_sysprefs`. Voeg aanpassingen toe in:

```
ansible/roles/koha_business_sysprefs/defaults/main.yml
```

en draai het bijbehorende playbook opnieuw. Zo blijft je configuratie reproduceerbaar bij een herinstallatie.

> Test eerst in de test-omgeving (`bib-test.marxisme.be`) voordat je naar productie gaat.

---

## 14.10 Volgende stappen

- [Doc 13](./13-circulatieregels-matrix.md) — voor de regels achter wat lezers via deze sysprefs proberen te doen.
- [Doc 15](./15-testscenario.md) — valideer dat OPAC-acties doen wat je verwacht.
