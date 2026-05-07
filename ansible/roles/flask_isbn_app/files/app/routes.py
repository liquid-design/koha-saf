"""
Flask routes voor ISBN -> MARCXML.

Flow:
  GET /                         -> form
  POST /lookup  (ISBN)          -> toon book data + form voor barcode/categories
  POST /save    (ISBN, barcode) -> schrijf MARCXML naar UPLOAD_DIR
"""

import os
from flask import current_app as app, render_template, request, flash, redirect, url_for

import isbn_lookup

# Staging dir waar Flask in mag schrijven. Cron leest hier uit.
# In productie: zorg dat zowel Flask-user als bib-koha hier read/write hebben.
UPLOAD_DIR = os.environ.get("KOHA_UPLOAD_DIR", "/var/lib/koha/bib/uploads")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", isbn=None, book=None, marcfile=None)


@app.route("/lookup", methods=["POST"])
def lookup():
    """Stap 1: ISBN opzoeken, resultaat tonen."""
    isbn = request.form.get("isbn", "").strip()
    if not isbn:
        flash("Geef een ISBN op.", "error")
        return redirect(url_for("index"))

    book_data = isbn_lookup.lookup_isbn(isbn)
    if not book_data:
        flash(f"Geen data gevonden voor ISBN {isbn}.", "error")
        return render_template("index.html", isbn=isbn, book=None, marcfile=None)

    return render_template("index.html", isbn=isbn, book=book_data, marcfile=None)


@app.route("/save", methods=["POST"])
def save():
    """Stap 2: barcode + (optioneel) aangepaste categorieen, schrijf XML."""
    isbn = request.form.get("isbn", "").strip()
    barcode = request.form.get("barcode", "").strip()
    category_input = request.form.get("category", "").strip()

    if not isbn or not barcode:
        flash("ISBN en barcode zijn verplicht.", "error")
        return redirect(url_for("index"))

    # Boekgegevens opnieuw ophalen (we vertrouwen niet op verborgen form-data)
    book_data = isbn_lookup.lookup_isbn(isbn)
    if not book_data:
        flash(f"Geen data gevonden voor ISBN {isbn}.", "error")
        return render_template("index.html", isbn=isbn, book=None, marcfile=None)

    # Override categorieen indien meegegeven (komma of puntkomma gescheiden)
    if category_input:
        categories = [
            c.strip()
            for c in category_input.replace(";", ",").split(",")
            if c.strip()
        ]
        book_data["categories"] = categories

    # Schrijf direct naar UPLOAD_DIR. write_marcxml maakt dir aan indien nodig.
    # Bestandsnaam bevat ISBN + barcode -> uniek per item, geen race conditions.
    try:
        output_file = isbn_lookup.write_marcxml(
            book_data, isbn, barcode, output_dir=UPLOAD_DIR
        )
    except PermissionError as e:
        flash(f"Geen schrijfrechten op {UPLOAD_DIR}: {e}", "error")
        return render_template("index.html", isbn=isbn, book=book_data, marcfile=None)
    except Exception as e:
        flash(f"Fout bij genereren XML: {e}", "error")
        return render_template("index.html", isbn=isbn, book=book_data, marcfile=None)

    if not output_file:
        flash("Genereren van MARCXML mislukt.", "error")
        return render_template("index.html", isbn=isbn, book=book_data, marcfile=None)

    marcfile = os.path.basename(output_file)
    flash(f"Opgeslagen: {marcfile}. Cron pikt het op binnen 1 minuut.", "success")
    return render_template("index.html", isbn=isbn, book=book_data, marcfile=marcfile)
