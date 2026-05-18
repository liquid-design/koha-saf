# 26.4.X Meertaligheid — NL/FR/EN interface

**Status:** addendum bij doc 26, mei 2026.

## Achtergrond

SAF heeft beheerders met Nederlandse, Franse en Engelse als
voorkeurstaal. De collectie is overwegend Nederlandstalig en Engelstalig,
met substantiële Franstalige werken en enkele Duitse uitgaven.

Bij de oorspronkelijke configuratie was alleen Nederlands actief. Dit
addendum activeert NL/FR/EN voor zowel OPAC-bezoekers als
medewerkers in de staff client.

## Wat dit vereist op installatieniveau

Koha installeert standaard alleen de Engelse interface. Wil je
Nederlands of Frans, dan moet je twee dingen doen:

1. **Translation files installeren** via `koha-translate --install <code>`.
   Dit genereert de templates uit `.po`-bestanden in de Koha-bron.
2. **Pas dan via sysprefs** activeren met `OPACLanguages` en
   `StaffInterfaceLanguages`.

Zonder stap 1 zien gebruikers de taal-dropdown maar valt Koha terug op
Engels — verwarrend en moeilijk te diagnosticeren.

Daarom is er een nieuwe Ansible-role `koha_languages` die stap 1 doet,
en draait die vóór `koha_business_sysprefs` in playbook 07.

## Wat we activeren

| Code | Taal | Voor |
|---|---|---|
| `nl-NL` | Nederlands | Default voor Belgisch publiek |
| `fr-FR` | Frans | Belgisch Franstalige beheerders en lezers |
| `en` | Engels | Engelstalige werken en internationale lezers |

**Niet geactiveerd**: `de-DE` (Duits). De Duitse werken in de collectie
zijn beperkt en Duitstalige lezers kunnen prima uit de voeten met de
Engelse of Nederlandse interface. Eventueel later toevoegen door
`de-DE` aan `koha_languages` lijst toe te voegen + `OPACLanguages` /
`StaffInterfaceLanguages` uit te breiden.

**Niet beschikbaar**: Belgisch Nederlands of Belgisch Frans als aparte
codes. Koha gebruikt `nl-NL` en `fr-FR` voor het hele taalgebied —
afwijkingen tussen NL/BE en FR/BE Nederlands / Frans worden niet
weerspiegeld.

## Bijgewerkte sysprefs

```yaml
- pref: language
  value: "nl-NL"              # default bij eerste OPAC-bezoek

- pref: OPACLanguages
  value: "nl-NL|fr-FR|en"     # pipe-separated, niet komma!

- pref: opaclanguagesdisplay
  value: "1"                  # toon taalswitcher in OPAC

- pref: StaffInterfaceLanguages
  value: "nl-NL|fr-FR|en"

- pref: TranslateNotices
  value: "1"                  # notices in patron's voorkeurstaal

- pref: AddressFormat
  value: "frenchstyle"        # dichtst bij BE-conventie

- pref: FacetSortingLocale
  value: "nl_BE"              # unicode-bewuste sortering voor accenten
```

## Hoe medewerker/lezer zijn taal kiest

- **OPAC-bezoekers**: taal-dropdown rechtsboven op elke pagina van de
  OPAC. Wordt onthouden via cookie.
- **Staff client medewerkers**: rechtsboven, naast de logout-knop.
  Wordt opgeslagen per gebruikersaccount.
- **Per-patron notice-taal**: in staff client bij patron-detail →
  Edit → "Preferred language for notices". Bepaalt welke taal-variant
  van een notice template wordt gestuurd.

## Wat er nog moet gebeuren (handmatig of in vervolgwerk)

`TranslateNotices=1` activeert de **mogelijkheid** om notices per taal
te leveren, maar je moet de vertalingen zelf nog aanmaken in:

```
Tools → Notices and slips
```

Voor elke notice template kun je een NL/FR/EN variant invoeren. Koha
bepaalt welke variant gebruikt wordt op basis van de patron-voorkeur,
met fallback op `language` (de OPAC default = `nl-NL`) als er voor
de patron-taal geen vertaling bestaat.

Plan: na een paar weken proefdraaien, kijken welke notices feitelijk
verzonden worden, en daarvan NL/FR/EN versies maken. Niet alles
vooraf vertalen — veel templates worden nooit gebruikt.

## Smoke test na deploy

1. `https://bib-test.marxisme.be` openen — taal-dropdown rechtsboven
   met NL/FR/EN keuze
2. Switch naar Frans — UI moet in het Frans omschakelen
3. Switch naar Engels — UI moet in het Engels omschakelen
4. `https://bib-test-intra.marxisme.be` inloggen — zelfde drie talen
   beschikbaar in profile-menu rechtsboven
5. SQL-check:
   ```bash
   sudo koha-mysql bib <<EOF
   SELECT variable, value FROM systempreferences
   WHERE variable IN ('OPACLanguages', 'StaffInterfaceLanguages',
                      'language', 'TranslateNotices');
   EOF
   ```
   Moet pipe-separated waarden tonen, geen comma's.

## Disk-impact

Per taal ~30 MB aan templates. NL+FR samen ~60 MB extra. Verwaarloosbaar.

## Updates bij Koha-upgrades

Bij een minor of major Koha-upgrade kunnen `.po` files wijzigen.
De `koha_languages` role draait `koha-translate --install` opnieuw bij
elke run, wat templates verfrist. Idempotent: als de versie al goed is,
geen no-op behalve een idempotency-check.
