"""
Bron-registratie en lookup.

Om een nieuwe bron toe te voegen:
1. Maak een module in deze map die Source subclasst
2. Importeer hem hieronder en voeg toe aan SOURCES

De volgorde in SOURCES bepaalt de display-volgorde in de UI
(meest betrouwbare/relevante eerst voor SAF-collectieprofiel).
"""

from concurrent.futures import ThreadPoolExecutor

from .base import BookRecord, Source
from .kb_nl import KbNlSource
from .k10plus import K10plusSource
from .dnb import DnbSource
from .loc import LocSource
from .bnf import BnfSource
from .google_books import GoogleBooksSource
from .openlibrary import OpenLibrarySource


# Volgorde = display-volgorde in UI. Aanpassen wijzigt niets aan
# de lookup-logica (alles wordt parallel bevraagd).
SOURCES: list[Source] = [
    KbNlSource(),
    K10plusSource(),
    DnbSource(),
    LocSource(),
    BnfSource(),
    GoogleBooksSource(),
    OpenLibrarySource(),
]


def lookup_all(isbn: str) -> list[BookRecord]:
    """
    Bevraag alle bronnen parallel voor één ISBN.

    Returnt altijd evenveel records als er bronnen zijn, in dezelfde
    volgorde. Records met found=False zijn misses (de UI filtert die).
    Een falende bron geeft rec.error gevuld; nooit een exception naar buiten.
    """
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as ex:
        futures = [(src, ex.submit(src.lookup, isbn)) for src in SOURCES]
        return [fut.result() for _, fut in futures]


def get_hits(records: list[BookRecord]) -> list[BookRecord]:
    """Filter alleen succesvolle hits voor UI presentatie."""
    return [r for r in records if r.found]
