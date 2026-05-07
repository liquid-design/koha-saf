#!/usr/bin/env python3
"""
ISBN lookup -> MARCXML voor Koha import.

Strategie:
- Haal data van OpenLibrary + Google Books
- Merge resultaten (Google heeft vaak rijkere data, OpenLibrary is fallback)
- Bouw een MARC21 record met VERPLICHTE velden voor Koha:
    Leader, 020 (ISBN), 100 (auteur), 245 (titel),
    942$c (record-level item type),
    952 (item info: branch, item type, barcode)
"""

import os
import sys
import requests
from rich import print
from rich.table import Table
from pymarc import Record, Field, Subfield, XMLWriter

# ---------------------------------------------------------------------------
# Constanten - pas aan per omgeving
# ---------------------------------------------------------------------------
DEFAULT_BRANCH = "SAF"        # branchcode uit koha_business_libraries
DEFAULT_ITEMTYPE = "BK"        # uit koha_business_item_types
DEFAULT_CLASS_SOURCE = "z"     # 'z' = custom, 'ddc' = Dewey, 'lcc' = LoC


# ---------------------------------------------------------------------------
# API fetchers
# ---------------------------------------------------------------------------
def fetch_openlibrary(isbn):
    """Query OpenLibrary API for a given ISBN."""
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        key = f"ISBN:{isbn}"
        if key not in data:
            return {}
        book = data[key]
        return {
            "title": book.get("title"),
            "subtitle": book.get("subtitle"),
            "authors": [a["name"] for a in book.get("authors", [])],
            "publish_date": book.get("publish_date"),
            "publishers": [p["name"] for p in book.get("publishers", [])],
            "cover": (book.get("cover", {}) or {}).get("large")
                     or (book.get("cover", {}) or {}).get("medium"),
            "source": "OpenLibrary",
        }
    except Exception as e:
        print(f"[red]OpenLibrary error:[/red] {e}")
        return {}


def fetch_googlebooks(isbn):
    """Query Google Books API for a given ISBN."""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "items" not in data:
            return {}
        info = data["items"][0]["volumeInfo"]
        return {
            "title": info.get("title"),
            "subtitle": info.get("subtitle"),
            "authors": info.get("authors"),
            "publish_date": info.get("publishedDate"),
            "publishers": [info.get("publisher")] if info.get("publisher") else [],
            "cover": (info.get("imageLinks", {}) or {}).get("thumbnail"),
            "pagecount": info.get("pageCount"),
            "categories": info.get("categories"),
            "language": info.get("language"),
            "description": info.get("description"),
            "source": "GoogleBooks",
        }
    except Exception as e:
        print(f"[red]Google Books error:[/red] {e}")
        return {}


def merge_results(ol_data, gb_data):
    """Combine results: Google Books first, OpenLibrary as fallback."""
    if not ol_data and not gb_data:
        return {}
    result = {}
    for key in set(ol_data.keys()).union(gb_data.keys()):
        result[key] = gb_data.get(key) or ol_data.get(key)
    return result


def lookup_isbn(isbn):
    """Used by Flask: fetch + merge, no XML write."""
    ol_data = fetch_openlibrary(isbn)
    gb_data = fetch_googlebooks(isbn)
    return merge_results(ol_data, gb_data)


# ---------------------------------------------------------------------------
# MARC21 record building
# ---------------------------------------------------------------------------
def create_marc_record(book_data, isbn, barcode,
                       branch=DEFAULT_BRANCH,
                       itemtype=DEFAULT_ITEMTYPE,
                       class_source=DEFAULT_CLASS_SOURCE):
    """
    Bouw een Koha-compatibel MARC21 record.

    Verplicht voor Koha:
      Leader, 020, 245, 942$c, en 952$2/$a/$b/$p/$y voor uitleen.
    """
    if not book_data:
        return None
    if not barcode:
        raise ValueError("Barcode is verplicht voor Koha-import (952$p)")

    record = Record(to_unicode=True, force_utf8=True)

    # Leader: posities zijn betekenisvol.
    # 'n' = new, 'a' = language material, 'm' = monograph
    record.leader = "00000nam a2200000 a 4500"

    # ----- Bibliografische velden -----

    # 020 ISBN
    record.add_field(Field(
        tag='020',
        indicators=[' ', ' '],
        subfields=[Subfield('a', isbn)],
    ))

    # 041 taal
    if book_data.get("language"):
        record.add_field(Field(
            tag='041',
            indicators=['0', ' '],
            subfields=[Subfield('a', book_data["language"])],
        ))

    # 100 auteur (eerste auteur)
    authors = book_data.get("authors") or []
    if authors:
        record.add_field(Field(
            tag='100',
            indicators=['1', ' '],
            subfields=[Subfield('a', authors[0])],
        ))

    # 245 titel + subtitel
    title = (book_data.get("title") or "").strip()
    if not title:
        title = "[Geen titel beschikbaar]"
    title_subfields = [Subfield('a', title)]
    subtitle = (book_data.get("subtitle") or "").strip()
    if subtitle:
        title_subfields.append(Subfield('b', subtitle))
    # 245 indicator 1 = '1' als er een 100 veld is, anders '0'
    ind1 = '1' if authors else '0'
    record.add_field(Field(
        tag='245',
        indicators=[ind1, '0'],
        subfields=title_subfields,
    ))

    # 264 publicatie (uitgever + jaar)
    publishers = book_data.get("publishers") or []
    pub_date = book_data.get("publish_date") or ""
    pub_subfields = []
    if publishers:
        pub_subfields.append(Subfield('b', ", ".join(publishers)))
    if pub_date:
        year = ''.join(c for c in pub_date[:4] if c.isdigit())
        if year:
            pub_subfields.append(Subfield('c', year))
    if pub_subfields:
        record.add_field(Field(
            tag='264',
            indicators=[' ', '1'],
            subfields=pub_subfields,
        ))

    # 300 fysieke beschrijving (paginas)
    if book_data.get("pagecount"):
        record.add_field(Field(
            tag='300',
            indicators=[' ', ' '],
            subfields=[Subfield('a', f"{book_data['pagecount']} p.")],
        ))

    # 520 beschrijving / samenvatting
    if book_data.get("description"):
        record.add_field(Field(
            tag='520',
            indicators=[' ', ' '],
            subfields=[Subfield('a', book_data["description"])],
        ))

    # 650 onderwerpen / categorieen
    for cat in (book_data.get("categories") or []):
        record.add_field(Field(
            tag='650',
            indicators=[' ', '0'],
            subfields=[Subfield('a', cat)],
        ))

    # ----- Koha-specifieke velden -----

    # 942$c is verplicht: default itemtype op record-niveau,
    # wordt gekopieerd naar 952$y bij item creation.
    record.add_field(Field(
        tag='942',
        indicators=[' ', ' '],
        subfields=[Subfield('c', itemtype)],
    ))

    # 952 Koha holdings/item info
    record.add_field(Field(
        tag='952',
        indicators=[' ', ' '],
        subfields=[
            Subfield('2', class_source),
            Subfield('a', branch),
            Subfield('b', branch),
            Subfield('p', barcode),
            Subfield('y', itemtype),
        ],
    ))

    return record


def _record_to_marcxml(record):
    """
    Genereer MARCXML met de juiste attribuut-volgorde (tag eerst, dan
    indicators). pymarc's XMLWriter sorteert alfabetisch (ind1, ind2, tag)
    wat sommige Perl-based parsers laat falen met
    'Use of uninitialized value $tag'. Daarom schrijven we zelf.

    Genereert exact wat Koha's eigen marc_to_marcxml output zou doen.
    """
    from xml.sax.saxutils import escape

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<collection xmlns="http://www.loc.gov/MARC21/slim">')
    parts.append('<record>')

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
            ind1 = (field.indicator1 or " ")
            ind2 = (field.indicator2 or " ")
            # Attribuut-volgorde: tag, ind1, ind2 (niet alfabetisch!)
            parts.append(
                f'  <datafield tag="{tag}" ind1="{ind1}" ind2="{ind2}">'
            )
            for sf in field.subfields:
                code = sf.code
                value = escape(sf.value)
                parts.append(
                    f'    <subfield code="{code}">{value}</subfield>'
                )
            parts.append('  </datafield>')

    parts.append('</record>')
    parts.append('</collection>')
    return "\n".join(parts) + "\n"


def write_marcxml(book_data, isbn, barcode, output_dir=".", **kwargs):
    """Schrijf MARCXML, return het volledige pad."""
    record = create_marc_record(book_data, isbn, barcode, **kwargs)
    if not record:
        print(f"[red]Geen MARC-record gemaakt voor {isbn}[/red]")
        return None

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{isbn}_{barcode}.xml")
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(_record_to_marcxml(record))
    print(f"[green]MARCXML aangemaakt:[/green] {output_file}")
    return output_file


# ---------------------------------------------------------------------------
# Helpers voor CLI gebruik
# ---------------------------------------------------------------------------
def show_table(book):
    table = Table(title="Book Information", show_lines=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    for k, v in book.items():
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v)
        table.add_row(k, str(v) if v is not None else "")
    print(table)


# ---------------------------------------------------------------------------
# CLI entrypoint - handig om los te testen zonder Flask
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[yellow]Usage:[/yellow] python isbn_lookup.py <ISBN> <BARCODE>")
        print("       python isbn_lookup.py 9780140445695 SAF000001")
        sys.exit(1)

    isbn = sys.argv[1].strip()
    barcode = sys.argv[2].strip()

    print(f"[bold blue]Looking up ISBN {isbn}...[/bold blue]")

    merged = lookup_isbn(isbn)
    if not merged:
        print("[red]Geen informatie gevonden voor dit ISBN.[/red]")
        sys.exit(1)

    show_table(merged)
    write_marcxml(merged, isbn, barcode, output_dir="./xml_output")