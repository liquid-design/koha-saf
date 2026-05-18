"""
Gemeenschappelijke basis voor alle ISBN-bronnen.

BookRecord = uniforme datastructuur die elke bron retourneert.
Source = abstract base waar elke bron van erft.

Door alle bronnen hetzelfde object te laten teruggeven kan de merger
ze blind combineren zonder per-bron kennis.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
from abc import ABC, abstractmethod


@dataclass
class BookRecord:
    """
    Genormaliseerde bibliografische data van één bron.

    Velden die niet door een bron worden geleverd blijven None of lege list.
    De `source` veld toont welke bron dit record produceerde, wat de UI
    gebruikt om opties te tonen aan de bibliothecaris.
    """
    # Identificatie
    isbn: str = ""
    source: str = ""  # bv. "KB-NL", "K10plus"

    # Bibliografisch
    title: Optional[str] = None
    subtitle: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    publishers: list[str] = field(default_factory=list)
    publish_place: Optional[str] = None
    publish_date: Optional[str] = None    # jaar als string, bv. "2001"
    language: Optional[str] = None         # ISO 639-3, bv. "nld", "fre", "eng"
    pagecount: Optional[int] = None
    description: Optional[str] = None      # samenvatting / flaptekst (MARC 520)
    categories: list[str] = field(default_factory=list)  # onderwerpen, MARC 650
    cover: Optional[str] = None            # URL naar cover-afbeelding

    # Metadata over de fetch zelf
    found: bool = False                    # True als bron data leverde
    error: Optional[str] = None            # foutmelding indien fetch faalde
    fetch_ms: Optional[int] = None         # hoe lang de fetch duurde

    def is_empty(self) -> bool:
        """True als geen enkel bibliografisch veld is ingevuld."""
        return not any([
            self.title, self.subtitle, self.authors,
            self.publishers, self.description,
        ])

    def to_dict(self) -> dict:
        """Voor JSON-serialisatie en Jinja templates."""
        return asdict(self)


class Source(ABC):
    """
    Abstract base voor een ISBN-bron.

    Subclasses implementeren `_fetch(isbn)` en geven een BookRecord terug.
    De `lookup(isbn)` wrapper handelt timing en error handling af, zodat
    individuele sources zich daar niet om hoeven te bekommeren.
    """

    name: str = "abstract"  # subclasses overriden dit
    timeout: int = 5         # seconden per HTTP call

    def lookup(self, isbn: str) -> BookRecord:
        """
        Publieke entry point: wrap _fetch met timing en exception-vangst.

        Een falende bron mag nooit de hele lookup-flow breken — we
        retourneren altijd een BookRecord, met error-veld indien nodig.
        """
        import time
        rec = BookRecord(isbn=isbn, source=self.name)
        t0 = time.monotonic()
        try:
            self._fetch(isbn, rec)
        except Exception as e:
            rec.error = f"{type(e).__name__}: {e}"
        rec.fetch_ms = int((time.monotonic() - t0) * 1000)
        return rec

    @abstractmethod
    def _fetch(self, isbn: str, rec: BookRecord) -> None:
        """
        Implementeer per bron: vul `rec` met data.

        Zet rec.found=True bij een succesvolle hit. Laat rec.found=False
        bij MISS (en eventueel rec.error voor diagnostiek).
        """
        ...


# ---------------------------------------------------------------------------
# Helpers gebruikt door meerdere bronnen
# ---------------------------------------------------------------------------
def extract_year(text: Optional[str]) -> Optional[str]:
    """
    Haal een 4-cijferig jaar uit een string.

    Werkt voor:
      "2001"           -> "2001"
      "DL 2019"        -> "2019" (BnF quirk)
      "[2019]"         -> "2019"
      "2024-03-15"     -> "2024"
      "c2001"          -> "2001"
      "20240117..."    -> "2024" (KB-NL catalog timestamp quirk)

    None of geen 4 cijfers gevonden -> None.
    """
    if not text:
        return None
    import re
    m = re.search(r"\b(1[5-9]\d{2}|20[0-9]{2}|21\d{2})\b", str(text))
    return m.group(1) if m else None


def normalize_language(lang: Optional[str]) -> Optional[str]:
    """
    Converteer 2-letter ISO 639-1 naar 3-letter ISO 639-3 (Koha-norm).

    Onbekende of al-3-letter codes worden lowercase teruggegeven.
    """
    if not lang:
        return None
    lang = lang.strip().lower()
    mapping = {
        "nl": "nld", "en": "eng", "fr": "fre", "de": "ger",
        "es": "spa", "it": "ita", "pt": "por", "ru": "rus",
        "ar": "ara", "zh": "chi", "ja": "jpn", "tr": "tur",
        "pl": "pol", "sv": "swe", "no": "nor", "da": "dan",
        "fi": "fin", "cs": "cze", "hu": "hun", "el": "gre",
    }
    return mapping.get(lang, lang)
