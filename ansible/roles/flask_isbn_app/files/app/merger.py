"""
Source merger.

De gebruiker kiest maximaal 2 bronnen om te combineren. Deze module
voert die merge uit: voor elk veld geldt 'eerste niet-lege wint',
waarbij de volgorde van de primary/secondary lijst de prioriteit bepaalt.

Voorbeeld: primary=KB-NL, secondary=K10plus
  -> titel: KB-NL als die er is, anders K10plus
  -> samenvatting: K10plus als KB-NL er geen heeft

Voor list-velden (authors, publishers, categories) wordt unie genomen
zonder duplicates.
"""

from .sources.base import BookRecord


def merge_records(primary: BookRecord, secondary: BookRecord | None = None) -> BookRecord:
    """
    Merge primary met (optioneel) secondary.

    Primary heeft voorrang voor scalar velden. Voor list velden worden
    de waarden gecombineerd (primary eerst, dan unieke uit secondary).
    """
    merged = BookRecord(
        isbn=primary.isbn,
        source=primary.source if secondary is None else f"{primary.source} + {secondary.source}",
        found=True,
    )

    # Scalar velden: primary wint, secondary vult op
    for attr in ("title", "subtitle", "publish_place", "publish_date",
                 "language", "pagecount", "description", "cover"):
        val = getattr(primary, attr)
        if not val and secondary:
            val = getattr(secondary, attr)
        setattr(merged, attr, val)

    # List velden: unie zonder duplicates, primary eerst
    for attr in ("authors", "publishers", "categories"):
        combined = list(getattr(primary, attr))
        if secondary:
            for v in getattr(secondary, attr):
                if v not in combined:
                    combined.append(v)
        setattr(merged, attr, combined)

    return merged


def find_record(records: list[BookRecord], source_name: str) -> BookRecord | None:
    """Vind een record uit een lijst op basis van source-naam."""
    for r in records:
        if r.source == source_name:
            return r
    return None
