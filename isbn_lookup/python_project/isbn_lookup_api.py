#!/usr/bin/env python3
import requests
import sys
from rich import print
from rich.table import Table
from pymarc import Record, Field, Subfield, XMLWriter
import random      # NIEUW: voor automatische barcodes
import string      # NIEUW: voor automatische barcodes

def fetch_openlibrary(isbn):
    """Query OpenLibrary API for een gegeven ISBN"""
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
            "authors": [a["name"] for a in book.get("authors", [])],
            "publish_date": book.get("publish_date"),
            "publishers": [p["name"] for p in book.get("publishers", [])],
            "cover": book.get("cover", {}).get("large") or book.get("cover", {}).get("medium"),
            "source": "OpenLibrary"
        }
    except Exception as e:
        print(f"[red]OpenLibrary error:[/red] {e}")
        return {}

def fetch_googlebooks(isbn):
    """Query Google Books API for een gegeven ISBN"""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "items" not in data:
            return {}
        info = data["items"][0]["volumeInfo"]
        return {
            "title": info.get("title"),
            "authors": info.get("authors"),
            "publish_date": info.get("publishedDate"),
            "publishers": [info.get("publisher")] if info.get("publisher") else [],
            "cover": info.get("imageLinks", {}).get("thumbnail"),
            "pagecount": info.get("pageCount"),
            "categories": info.get("categories"),
            "language": info.get("language"),
            "description": info.get("description"),
            "source": "GoogleBooks"
        }
    except Exception as e:
        print(f"[red]Google Books error:[/red] {e}")
        return {}

def merge_results(ol_data, gb_data):
    """Combine results from both sources intelligently"""
    result = {}
    for key in set(ol_data.keys()).union(gb_data.keys()):
        result[key] = gb_data.get(key) or ol_data.get(key)
    # prefer OpenLibrary cover if Google’s is missing
    if not result.get("cover") and ol_data.get("cover"):
        result["cover"] = ol_data["cover"]
    return result

def show_table(book):
    """Pretty print book info"""
    table = Table(title="📚 Book Information", show_lines=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    for k, v in book.items():
        if isinstance(v, list):
            v = ", ".join(v)
        table.add_row(k, str(v))
    print(table)

def create_marcxml_record(book_data, isbn):
    """Maak een MARCXML Record van de gecombineerde boekdata"""
    record = Record(to_unicode=True, force_utf8=True)

    # Leader correct voor Koha
    record.leader = "00000nam a2200000 a 4500"

    if not book_data:
        return None

    # 020 ISBN
    record.add_field(
        Field(tag='020', indicators=[' ', ' '], subfields=[Subfield('a', isbn)])
    )

    # 100 Auteur
    if book_data.get("authors"):
        record.add_field(
            Field(tag='100', indicators=['1',' '], subfields=[Subfield('a', book_data["authors"][0])])
        )

    # 245 Titel + eventueel subtitel
    title = book_data.get("title", "")
    subtitle = book_data.get("subtitle")
    full_title = f"{title} : {subtitle}" if subtitle else title
    record.add_field(
        Field(tag='245', indicators=['1','0'], subfields=[Subfield('a', full_title)])
    )

    # 264 Uitgever + jaartal
    publisher = book_data.get("publishers")
    publishedDate = book_data.get("publish_date")
    subfields = []
    if publisher:
        subfields.append(Subfield('b', ", ".join(publisher)))
    if publishedDate:
        subfields.append(Subfield('c', publishedDate[:4]))
    if subfields:
        record.add_field(Field(tag='264', indicators=[' ','1'], subfields=subfields))

    # 650 Categorieën
    for cat in (book_data.get("categories") or []):
        record.add_field(Field(tag='650', indicators=[' ','0'], subfields=[Subfield('a', cat)]))

    # 300 Pagina's
    #if book_data.get("pageCount"):
    #    record.add_field(Field(tag='300', indicators=[' ',' '], subfields=[Subfield('a', str(book_data["pageCount"]) + " p.")]))

    # 041 Taal
    if book_data.get("language"):
        record.add_field(Field(tag='041', indicators=['0',' '], subfields=[Subfield('a', book_data["language"])]))

    return record

def write_marcxml(book_data, isbn):
    """Schrijf één MARCXML bestand per ISBN"""
    record = create_marcxml_record(book_data, isbn)
    if not record:
        print(f"[red]Geen MARC-record gemaakt voor {isbn}[/red]")
        return
    output_file = f"{isbn}.xml"
    with open(output_file, "wb") as fh:
        writer = XMLWriter(fh)
        writer.write(record)
        writer.close()
    print(f"[green]✅ MARCXML-bestand aangemaakt:[/green] {output_file}")
    return output_file

def lookup_isbn(isbn):
    """Gebruik dit vanuit Flask: haalt en merged API-data"""
    ol_data = fetch_openlibrary(isbn)
    gb_data = fetch_googlebooks(isbn)
    merged = merge_results(ol_data, gb_data)
    return merged

# ==========================
# NIEUW: Koha REST API functies
# ==========================

KOHA_BASE = "http://<koha-server>/api/v1"   # NIEUW: vul jouw Koha server in
API_KEY = "<jouw_api_key>"                  # NIEUW: API key
LIBRARY = "<bibliotheek_code>"              # NIEUW: bv. MAIN
ITEM_TYPE = "Book"                          # NIEUW: itemtype
ITEM_LOCATION = "Main"                       # NIEUW: locatie
ITEM_STATUS = "Available"                    # NIEUW: status

def import_marcxml_to_koha(file_path):
    """NIEUW: Importeer MARCXML in Koha via REST API"""
    url = f"{KOHA_BASE}/biblio/import_marcxml"
    headers = {"Authorization": API_KEY}
    with open(file_path, "rb") as f:
        files = {'file': f}
        resp = requests.post(url, files=files, headers=headers)
    if resp.status_code == 201:
        biblio_id = resp.json().get("biblionumber")
        print(f"[green]✅ Bibliografisch record aangemaakt in Koha: {biblio_id}[/green]")
        return biblio_id
    else:
        print(f"[red]❌ Fout bij import MARCXML: {resp.text}[/red]")
        return None

def create_item_in_koha(biblio_id, barcode=None):
    """NIEUW: Maak automatisch één item/exemplaar aan voor een bibliografisch record"""
    url = f"{KOHA_BASE}/items"
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}

    if not barcode:
        barcode = ''.join(random.choices(string.digits, k=13))  # automatische barcode

    payload = {
        "biblionumber": biblio_id,
        "branchcode": LIBRARY,
        "itemtype": ITEM_TYPE,
        "location": ITEM_LOCATION,
        "barcode": barcode,
        "status": ITEM_STATUS,
        "opacvisible": "y"   # zichtbaar in OPAC
    }

    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 201:
        print(f"[green]✅ Item aangemaakt: {barcode}[/green]")
    else:
        print(f"[red]❌ Fout bij aanmaken item: {resp.text}[/red]")

# ==========================
# Main script
# ==========================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[yellow]Usage:[/yellow] python isbn_lookup.py [ISBN]")
        sys.exit(1)

    isbn = sys.argv[1].strip()
    print(f"[bold blue]🔎 Looking up ISBN {isbn}...[/bold blue]")

    # Ophalen van api bronnen
    ol_data = fetch_openlibrary(isbn)
    gb_data = fetch_googlebooks(isbn)
    merged = merge_results(ol_data, gb_data)

    # Ruwe data vóór merging
    print("\n[bold cyan]--- OpenLibrary data ---[/bold cyan]")
    print(ol_data if ol_data else "[red]Geen data ontvangen[/red]")

    print("\n[bold magenta]--- Google Books data ---[/bold magenta]")
    print(gb_data if gb_data else "[red]Geen data ontvangen[/red]")

    # Mergen van resultaten
    if merged:
        show_table(merged)
        marc_file = write_marcxml(merged, isbn)

        # NIEUW: importeer MARCXML in Koha
        if marc_file:
            biblio_id = import_marcxml_to_koha(marc_file)

            # NIEUW: maak automatisch één item aan
            if biblio_id:
                create_item_in_koha(biblio_id)

    else:
        print("[red]No information found.[/red]")
        sys.exit(0)

    show_table(merged)
