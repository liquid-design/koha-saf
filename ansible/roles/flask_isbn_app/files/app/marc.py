"""
MARC21 record builder voor Koha import.

Bouwt een MARC21 record uit een BookRecord en schrijft het als MARCXML
met de attribuut-volgorde die Koha's Perl-parser verwacht (tag, ind1, ind2;
NIET alfabetisch zoals pymarc default doet).
"""

import os
from xml.sax.saxutils import escape
from pymarc import Record, Field, Subfield

from .sources.base import BookRecord


# Koha-specifieke defaults voor SAF
DEFAULT_BRANCH = "SAF"
DEFAULT_ITEMTYPE = "BK"
DEFAULT_CLASS_SOURCE = "z"  # 'z' = custom, 'ddc' = Dewey, 'lcc' = LoC


def build_record(book: BookRecord, isbn: str, barcode: str,
                 categories: list[str] | None = None,
                 branch: str = DEFAULT_BRANCH,
                 itemtype: str = DEFAULT_ITEMTYPE,
                 class_source: str = DEFAULT_CLASS_SOURCE) -> Record:
    """
    Bouw een Koha-compatibel MARC21 record.

    Verplichte velden voor Koha: Leader, 020, 245, 942$c, en
    952$2/$a/$b/$p/$y voor uitleen.

    `categories` overschrijft book.categories indien meegegeven
    (komt typisch uit de SAF-dropdown selectie).
    """
    if not barcode:
        raise ValueError("Barcode is verplicht voor Koha-import (952$p)")

    record = Record(to_unicode=True, force_utf8=True)

    # Leader: 'n' = new, 'a' = language material, 'm' = monograph
    record.leader = "00000nam a2200000 a 4500"

    # ---- Bibliografische velden ----

    # 020 ISBN
    record.add_field(Field(
        tag="020", indicators=[" ", " "],
        subfields=[Subfield("a", isbn)],
    ))

    # 041 taal
    if book.language:
        record.add_field(Field(
            tag="041", indicators=["0", " "],
            subfields=[Subfield("a", book.language)],
        ))

    # 100 hoofdauteur
    if book.authors:
        record.add_field(Field(
            tag="100", indicators=["1", " "],
            subfields=[Subfield("a", book.authors[0])],
        ))

    # 245 titel + ondertitel
    title = (book.title or "[Geen titel beschikbaar]").strip()
    title_subfields = [Subfield("a", title)]
    if book.subtitle:
        title_subfields.append(Subfield("b", book.subtitle.strip()))
    ind1 = "1" if book.authors else "0"
    record.add_field(Field(
        tag="245", indicators=[ind1, "0"],
        subfields=title_subfields,
    ))

    # 264 publicatie
    pub_subfields = []
    if book.publish_place:
        pub_subfields.append(Subfield("a", book.publish_place))
    if book.publishers:
        pub_subfields.append(Subfield("b", ", ".join(book.publishers)))
    if book.publish_date:
        pub_subfields.append(Subfield("c", book.publish_date))
    if pub_subfields:
        record.add_field(Field(
            tag="264", indicators=[" ", "1"],
            subfields=pub_subfields,
        ))

    # 300 fysieke beschrijving
    if book.pagecount:
        record.add_field(Field(
            tag="300", indicators=[" ", " "],
            subfields=[Subfield("a", f"{book.pagecount} p.")],
        ))

    # 520 samenvatting
    if book.description:
        record.add_field(Field(
            tag="520", indicators=[" ", " "],
            subfields=[Subfield("a", book.description)],
        ))

    # 700 mede-auteurs (alle behalve de eerste)
    for author in book.authors[1:]:
        record.add_field(Field(
            tag="700", indicators=["1", " "],
            subfields=[Subfield("a", author)],
        ))

    # 650 onderwerpen / categorieen
    # SAF-dropdown levert lowercase, doorzoekbaar in Koha facets
    cats_to_use = categories if categories is not None else book.categories
    for cat in cats_to_use:
        record.add_field(Field(
            tag="650", indicators=[" ", "0"],
            subfields=[Subfield("a", cat)],
        ))

    # ---- Koha-specifieke velden ----

    # 942$c verplicht: default itemtype op record-niveau
    record.add_field(Field(
        tag="942", indicators=[" ", " "],
        subfields=[Subfield("c", itemtype)],
    ))

    # 952 Koha holdings/item info
    record.add_field(Field(
        tag="952", indicators=[" ", " "],
        subfields=[
            Subfield("2", class_source),
            Subfield("a", branch),
            Subfield("b", branch),
            Subfield("p", barcode),
            Subfield("y", itemtype),
        ],
    ))

    return record


def record_to_marcxml(record: Record) -> str:
    """
    Genereer MARCXML met attribuut-volgorde tag > ind1 > ind2.

    pymarc's XMLWriter sorteert alfabetisch (ind1, ind2, tag), wat sommige
    Perl-parsers laat falen met 'Use of uninitialized value $tag'. Daarom
    schrijven we zelf met de juiste volgorde.
    """
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<collection xmlns="http://www.loc.gov/MARC21/slim">',
        '<record>',
    ]

    leader = record.leader
    if hasattr(leader, "leader"):
        leader = leader.leader
    parts.append(f'  <leader>{escape(str(leader))}</leader>')

    for field in record.get_fields():
        tag = field.tag
        if field.is_control_field():
            value = escape(field.value())
            parts.append(f'  <controlfield tag="{tag}">{value}</controlfield>')
        else:
            ind1 = field.indicator1 or " "
            ind2 = field.indicator2 or " "
            parts.append(f'  <datafield tag="{tag}" ind1="{ind1}" ind2="{ind2}">')
            for sf in field.subfields:
                code = sf.code
                value = escape(sf.value)
                parts.append(f'    <subfield code="{code}">{value}</subfield>')
            parts.append("  </datafield>")

    parts.append("</record>")
    parts.append("</collection>")
    return "\n".join(parts) + "\n"


def write_marcxml(book: BookRecord, isbn: str, barcode: str,
                  output_dir: str,
                  categories: list[str] | None = None,
                  **kwargs) -> str:
    """
    Bouw + schrijf MARCXML naar output_dir. Returnt het volledige pad.
    """
    record = build_record(book, isbn, barcode, categories=categories, **kwargs)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{isbn}_{barcode}.xml")
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(record_to_marcxml(record))
    return output_file
