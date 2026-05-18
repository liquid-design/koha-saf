"""
SAF bibliotheek - definitieve categorielijst.

Onderhoud:
- label = wat de bibliothecaris ziet in de dropdown
- value = wat naar Koha gaat. Bij subcategorieen "hoofd,sub" zodat
  routes.py op komma splitst -> twee losse MARC 650-velden
  (beide doorzoekbaar in Koha facets).
- Alle values lowercase per beslissing bibliothecaris.

Wijzigen vereist alleen edit van dit bestand + Ansible deploy + service restart.
Geen template-aanpassing nodig.
"""

CATEGORIES: list[tuple[str, str]] = [
    ("Feminisme", "feminisme"),
    ("Filosofie", "filosofie"),
    ("Sociologie", "sociologie"),
    ("Economie", "economie"),
    ("Oostblok", "oostblok"),
    ("Joegoslavië", "joegoslavië"),
    ("Frankrijk", "frankrijk"),
    ("Biografieën", "biografieën"),
    ("Marxisme — Marx en Engels", "marxisme,marx en engels"),
    ("Marxisme — Lenin", "marxisme,lenin"),
    ("Marxisme — Trotski", "marxisme,trotski"),
    ("Marxisme — Algemeen", "marxisme,algemeen"),
    ("Anarchisme", "anarchisme"),
    ("Jodendom", "jodendom"),
    ("Verzet & collaboratie — Verzet en collaboratie in België",
     "verzet & collaboratie,verzet en collaboratie in belgië"),
    ("Verzet & collaboratie — Verzet en collaboratie in Frankrijk",
     "verzet & collaboratie,verzet en collaboratie in frankrijk"),
    ("Verzet & collaboratie — WO2 algemeen",
     "verzet & collaboratie,wo2 algemeen"),
    ("Actualiteit", "actualiteit"),
    ("Midden-Oosten", "midden-oosten"),
    ("Antifascisme — Extreemrechts Franstalig",
     "antifascisme,extreemrechts franstalig"),
    ("Antifascisme — Extreemrechts Engelstalig",
     "antifascisme,extreemrechts engelstalig"),
    ("Antifascisme — Extreemrechts Nederlandstalig",
     "antifascisme,extreemrechts nederlandstalig"),
    ("Antifascisme — Fascisme", "antifascisme,fascisme"),
    ("Antifascisme — VB en co", "antifascisme,vb en co"),
    ("Antifascisme — Antiracisme", "antifascisme,antiracisme"),
    ("Antifascisme — Dekolonisatie", "antifascisme,dekolonisatie"),
    ("Latijns-Amerika – Afrika – Azië",
     "latijns-amerika – afrika – azië"),
    ("Geschiedenis algemeen", "geschiedenis algemeen"),
    ("Geschiedenis België", "geschiedenis belgië"),
    ("Belgische arbeidersbeweging", "belgische arbeidersbeweging"),
    ("Communistische Partij", "communistische partij"),
    ("Sociaaldemocratie", "sociaaldemocratie"),
    ("VS", "vs"),
    ("Italië", "italië"),
    ("Portugal", "portugal"),
    ("Spanje", "spanje"),
    ("Griekenland", "griekenland"),
    ("Nederland", "nederland"),
    ("Duitsland – Oostenrijk – Zwitserland",
     "duitsland – oostenrijk – zwitserland"),
    ("Scandinavië", "scandinavië"),
    ("Groot-Brittannië", "groot-brittannië"),
    ("Fictie met een politieke inslag", "fictie met een politieke inslag"),
]


def split_category_value(value: str) -> list[str]:
    """
    'marxisme,trotski' -> ['marxisme', 'trotski']

    Splitst op komma en puntkomma zodat subcategorieën als losse
    MARC 650-velden in Koha terechtkomen (independently facet-searchable).
    """
    if not value:
        return []
    return [
        c.strip()
        for c in value.replace(";", ",").split(",")
        if c.strip()
    ]
