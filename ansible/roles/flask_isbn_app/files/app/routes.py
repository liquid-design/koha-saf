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

Alle session-state gaat via verborgen form-fields. Geen Flask session nodig.
"""

import os
import json
from flask import (
    current_app as app, render_template, request, flash,
    redirect, url_for, abort,
)

from .sources import lookup_all, get_hits
from .sources.base import BookRecord
from .merger import merge_records, find_record
from .marc import write_marcxml
from .categories import CATEGORIES, split_category_value


# Staging dir waar Flask in mag schrijven. Cron leest hier uit.
UPLOAD_DIR = os.environ.get("KOHA_UPLOAD_DIR", "/var/lib/koha-staging")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bookrecord_from_form(form) -> BookRecord:
    """
    Reconstrueer een BookRecord uit form-data van confirm.html.

    We vertrouwen geen verborgen form-fields blind: alle data wordt
    expliciet uit losse fields gehaald, niet uit een JSON-blob.
    """
    return BookRecord(
        isbn=form.get("isbn", "").strip(),
        source=form.get("source", "manueel"),
        title=form.get("title", "").strip() or None,
        subtitle=form.get("subtitle", "").strip() or None,
        authors=[a.strip() for a in form.get("authors", "").split(";") if a.strip()],
        publishers=[p.strip() for p in form.get("publishers", "").split(";") if p.strip()],
        publish_place=form.get("publish_place", "").strip() or None,
        publish_date=form.get("publish_date", "").strip() or None,
        language=form.get("language", "").strip() or None,
        pagecount=int(form["pagecount"]) if form.get("pagecount", "").isdigit() else None,
        description=form.get("description", "").strip() or None,
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
def lookup():
    """Stap 1: ISBN bij alle bronnen opzoeken."""
    isbn = request.form.get("isbn", "").strip().replace("-", "").replace(" ", "")
    if not isbn:
        flash("Geef een ISBN op.", "error")
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
def select():
    """
    Stap 2a: gebruiker heeft 1 of 2 bronnen geselecteerd in compare.html.

    Form-velden:
      isbn
      selected: list van source-namen (max 2)
    """
    isbn = request.form.get("isbn", "").strip()
    selected = request.form.getlist("selected")

    if not isbn:
        flash("ISBN ontbreekt.", "error")
        return redirect(url_for("index"))

    if len(selected) == 0:
        flash("Selecteer minstens één bron.", "error")
        # Bron opnieuw bevragen — eenvoudiger dan state bewaren
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
        isbn = request.args.get("isbn", "").strip()
    else:
        isbn = request.form.get("isbn", "").strip()

    if not isbn:
        flash("ISBN ontbreekt.", "error")
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
def save():
    """Stap 3: barcode + (eventueel aangepaste) data -> MARCXML schrijven."""
    isbn = request.form.get("isbn", "").strip()
    barcode = request.form.get("barcode", "").strip()
    category_value = request.form.get("category", "").strip()

    if not isbn or not barcode:
        flash("ISBN en barcode zijn verplicht.", "error")
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
