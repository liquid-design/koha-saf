"""
Flask routes voor ISBN -> MARCXML pipeline.

Flow:
  GET  /                  Startscherm: ISBN intypen/scannen
  POST /lookup            Bevraagt alle bronnen parallel, toont:
                          - alle hits naast elkaar (compare.html)
                          - of melding 'geen bron gevonden' met manueel-knop
                          - of bij precies 1 hit: direct doorsturen naar confirm
  POST /select            Gebruiker heeft 1 of 2 bronnen aangevinkt -> confirm
  GET  /manual?isbn=...   Leeg invulformulier (bij 0 hits of na knop-klik)
  POST /save              Schrijf MARCXML naar staging dir

Alle session-state gaat via verborgen form-fields. Geen Flask session nodig
voor data; sessie-cookie is alleen voor flash messages en CSRF token.

Security:
- /lookup en /select trekken externe SRU-bronnen aan -> 30/min per IP
- /save schrijft naar disk -> 10/min per IP
- ISBN en barcode worden strikt gevalideerd (regex) voor we ze in
  filenames of MARC velden zetten
- description wordt unicode-genormaliseerd en gelimiteerd op lengte
- CSRF tokens via Flask-WTF (zie __init__.py)
"""

import os
import re
import unicodedata
from flask import (
    current_app as app, render_template, request, flash,
    redirect, url_for,
)

from . import limiter
from .sources import lookup_all, get_hits
from .sources.base import BookRecord
from .merger import merge_records, find_record
from .marc import write_marcxml
from .categories import CATEGORIES, split_category_value


# Staging dir waar Flask in mag schrijven. Cron leest hier uit.
UPLOAD_DIR = os.environ.get("KOHA_UPLOAD_DIR", "/var/lib/koha-staging")

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
# ISBN: 10 of 13 cijfers, eventueel met X als 10e karakter (ISBN-10 checksum).
# We strippen al streepjes en spaties voor we matchen.
_ISBN_RE = re.compile(r"^(?:\d{9}[\dXx]|\d{13})$")

# Barcode: alleen alfanumeriek + _ en -, max 32 chars. Voldoende voor SAF-formaat
# 'SAF000001' en houdt path-traversal of MARC-injection volledig dicht.
_BARCODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

# Max lengtes voor vrije tekst-velden om absurde payloads te blokkeren.
# Echte bibliografische data zit ruim onder deze limieten.
_MAX_TITLE = 500
_MAX_SUBTITLE = 500
_MAX_AUTHORS = 1000        # joined string, niet per auteur
_MAX_PUBLISHERS = 500
_MAX_PLACE = 200
_MAX_DATE = 20
_MAX_LANG = 10
_MAX_DESCRIPTION = 10000   # flapteksten kunnen lang zijn, maar niet absurd


def _clean_text(value: str, max_len: int) -> str | None:
    """
    Normaliseer en limiteer een vrije-tekst veld.

    - NFC unicode normalisatie (zelfde karakter = zelfde bytes)
    - NULL bytes weghalen (kunnen Zebra indexer ontregelen)
    - Control characters weghalen behalve tab/newline
    - Truncaten op max_len
    - Lege string -> None

    Returnt None voor lege input zodat de MARC builder dat veld overslaat.
    """
    if not value:
        return None
    text = unicodedata.normalize("NFC", value)
    # Strip NULL bytes en andere control chars (behoud \t \n \r)
    text = "".join(
        c for c in text
        if c in ("\t", "\n", "\r") or unicodedata.category(c)[0] != "C"
    )
    text = text.strip()
    if not text:
        return None
    return text[:max_len]


def _normalize_isbn(raw: str) -> str:
    """Strip streepjes en spaties van een ISBN-string."""
    return raw.strip().replace("-", "").replace(" ", "")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bookrecord_from_form(form) -> BookRecord:
    """
    Reconstrueer een BookRecord uit form-data van confirm.html.

    We vertrouwen geen verborgen form-fields blind: alle data wordt
    expliciet uit losse fields gehaald, niet uit een JSON-blob. Alle
    tekstvelden gaan door _clean_text voor unicode normalisatie en
    lengte-limitering.
    """
    return BookRecord(
        isbn=_normalize_isbn(form.get("isbn", "")),
        source=_clean_text(form.get("source", "manueel"), 100) or "manueel",
        title=_clean_text(form.get("title", ""), _MAX_TITLE),
        subtitle=_clean_text(form.get("subtitle", ""), _MAX_SUBTITLE),
        authors=[
            a.strip()
            for a in (_clean_text(form.get("authors", ""), _MAX_AUTHORS) or "").split(";")
            if a.strip()
        ],
        publishers=[
            p.strip()
            for p in (_clean_text(form.get("publishers", ""), _MAX_PUBLISHERS) or "").split(";")
            if p.strip()
        ],
        publish_place=_clean_text(form.get("publish_place", ""), _MAX_PLACE),
        publish_date=_clean_text(form.get("publish_date", ""), _MAX_DATE),
        language=_clean_text(form.get("language", ""), _MAX_LANG),
        pagecount=int(form["pagecount"]) if form.get("pagecount", "").isdigit() else None,
        description=_clean_text(form.get("description", ""), _MAX_DESCRIPTION),
        found=True,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    """Startscherm: ISBN input."""
    return render_template("index.html")


@app.route("/lookup", methods=["POST"])
@limiter.limit("30 per minute")
def lookup():
    """Stap 1: ISBN bij alle bronnen opzoeken."""
    isbn = _normalize_isbn(request.form.get("isbn", ""))
    if not isbn:
        flash("Geef een ISBN op.", "error")
        return redirect(url_for("index"))

    if not _ISBN_RE.match(isbn):
        flash("Ongeldig ISBN (verwacht 10 of 13 cijfers).", "error")
        return redirect(url_for("index"))

    records = lookup_all(isbn)
    hits = get_hits(records)

    if len(hits) == 0:
        # Toon 'geen resultaten' scherm met manueel-knop én ISBN-correctie
        return render_template(
            "no_results.html",
            isbn=isbn,
            records=records,  # toont misses + errors voor diagnose
        )

    if len(hits) == 1:
        # Eén bron gevonden: meteen door naar bevestiging
        return render_template(
            "confirm.html",
            isbn=isbn,
            book=hits[0],
            categories=CATEGORIES,
        )

    # Meerdere bronnen: gebruiker kiest 1 of max 2
    return render_template(
        "compare.html",
        isbn=isbn,
        hits=hits,
        all_records=records,  # ook misses tonen onderaan
    )


@app.route("/select", methods=["POST"])
@limiter.limit("30 per minute")
def select():
    """
    Stap 2a: gebruiker heeft 1 of 2 bronnen geselecteerd in compare.html.

    Form-velden:
      isbn
      selected: list van source-namen (max 2)
    """
    isbn = _normalize_isbn(request.form.get("isbn", ""))
    selected = request.form.getlist("selected")

    if not isbn or not _ISBN_RE.match(isbn):
        flash("Ongeldig of ontbrekend ISBN.", "error")
        return redirect(url_for("index"))

    if len(selected) == 0:
        flash("Selecteer minstens één bron.", "error")
        return lookup()

    if len(selected) > 2:
        flash("Maximaal 2 bronnen tegelijk mergen.", "error")
        return lookup()

    # Opnieuw bevragen om verse data te krijgen
    # (gebruiker kan een paar minuten op compare-scherm hebben gestaan)
    records = lookup_all(isbn)
    primary = find_record(records, selected[0])
    if primary is None:
        flash(f"Bron '{selected[0]}' leverde geen data meer.", "error")
        return redirect(url_for("index"))

    secondary = find_record(records, selected[1]) if len(selected) == 2 else None
    merged = merge_records(primary, secondary)

    return render_template(
        "confirm.html",
        isbn=isbn,
        book=merged,
        categories=CATEGORIES,
    )


@app.route("/manual", methods=["GET", "POST"])
def manual():
    """Leeg invulformulier voor titels die in geen enkele bron staan."""
    if request.method == "GET":
        isbn = _normalize_isbn(request.args.get("isbn", ""))
    else:
        isbn = _normalize_isbn(request.form.get("isbn", ""))

    if not isbn or not _ISBN_RE.match(isbn):
        flash("Ongeldig of ontbrekend ISBN.", "error")
        return redirect(url_for("index"))

    # Lege BookRecord als template-input
    empty = BookRecord(isbn=isbn, source="manueel", found=True)

    return render_template(
        "confirm.html",
        isbn=isbn,
        book=empty,
        categories=CATEGORIES,
        is_manual=True,
    )


@app.route("/save", methods=["POST"])
@limiter.limit("10 per minute")
def save():
    """Stap 3: barcode + (eventueel aangepaste) data -> MARCXML schrijven."""
    isbn = _normalize_isbn(request.form.get("isbn", ""))
    barcode = request.form.get("barcode", "").strip()
    category_value = request.form.get("category", "").strip()

    # ISBN validatie
    if not isbn:
        flash("ISBN ontbreekt.", "error")
        return redirect(url_for("index"))
    if not _ISBN_RE.match(isbn):
        flash("Ongeldig ISBN (verwacht 10 of 13 cijfers).", "error")
        return redirect(url_for("index"))

    # Barcode validatie: strikt — wordt zowel in filename als MARC 952$p gebruikt
    if not barcode:
        flash("Barcode is verplicht.", "error")
        return redirect(url_for("index"))
    if not _BARCODE_RE.match(barcode):
        flash(
            "Ongeldige barcode (alleen letters, cijfers, _ en -, max 32 tekens).",
            "error",
        )
        # Bouw record uit form om de UI niet leeg te laten
        book = _bookrecord_from_form(request.form)
        return render_template(
            "confirm.html", isbn=isbn, book=book, categories=CATEGORIES,
        )

    # Category validatie: moet uit onze eigen lijst komen, anders weiger
    if category_value:
        allowed_values = {v for _, v in CATEGORIES}
        if category_value not in allowed_values:
            flash("Ongeldige categorie-waarde.", "error")
            return redirect(url_for("index"))

    # Bouw BookRecord uit de form-velden (gebruiker mocht editen)
    book = _bookrecord_from_form(request.form)

    # Categorieen: dropdown levert "hoofd,sub" -> splitsen tot 2 MARC 650
    categories = split_category_value(category_value) if category_value else None

    try:
        output_file = write_marcxml(
            book, isbn, barcode,
            output_dir=UPLOAD_DIR,
            categories=categories,
        )
    except PermissionError as e:
        flash(f"Geen schrijfrechten op {UPLOAD_DIR}: {e}", "error")
        return render_template("confirm.html", isbn=isbn, book=book,
                               categories=CATEGORIES)
    except Exception as e:
        flash(f"Fout bij genereren XML: {e}", "error")
        return render_template("confirm.html", isbn=isbn, book=book,
                               categories=CATEGORIES)

    marcfile = os.path.basename(output_file)
    flash(f"Opgeslagen: {marcfile}. Cron pikt het op binnen 1 minuut.", "success")
    return render_template("saved.html", isbn=isbn, marcfile=marcfile)
