from flask import current_app as app, render_template, request
import isbn_lookup
import os
import shutil
import pwd
import grp

UPLOAD_DIR = "/var/lib/koha/bib/uploads"


@app.route("/", methods=["GET", "POST"])
def index():
    book_data = None
    isbn = None

    # Eerste stap: ISBN lookup
    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        if isbn:
            book_data = isbn_lookup.lookup_isbn(isbn)

    # Hier tonen we enkel data, nog geen XML schrijven
    return render_template("index.html", isbn=isbn, book=book_data, marcfile=None)


@app.route("/save", methods=["POST"])
def save():
    isbn = request.form.get("isbn", "").strip()
    category_input = request.form.get("category", "").strip()

    if not isbn:
        return render_template("index.html", isbn=None, book=None, marcfile=None)

    # Boekgegevens opnieuw ophalen
    book_data = isbn_lookup.lookup_isbn(isbn)

    # ⬇️ User categorieën overschrijven
    if category_input:
        # meerdere categorieën scheiden met komma OF puntkomma
        categories = [
            c.strip()
            for c in category_input.replace(";", ",").split(",")
            if c.strip()
        ]
        book_data["categories"] = categories

    # MARCXML-bestandnaam
    marcfile = f"{isbn}.xml"
    temp_path = f"{isbn}.xml"
    output_path = os.path.join(UPLOAD_DIR, marcfile)

    # MARCXML-bestand aanmaken
    isbn_lookup.write_marcxml(book_data, isbn)

    # Verplaatsen naar Koha-uploadmap
    if not os.path.exists(output_path) and os.path.exists(temp_path):
        shutil.move(temp_path, output_path)

    # Bestandsrechten instellen
    try:
        uid = pwd.getpwnam("bib-koha").pw_uid
        gid = grp.getgrnam("bib-koha").gr_gid
        os.chown(output_path, uid, gid)
        os.chmod(output_path, 0o644)
    except Exception as e:
        print(f"⚠️ Waarschuwing: kon rechten niet instellen voor {output_path}: {e}")

    return render_template("index.html", isbn=isbn, book=book_data, marcfile=marcfile)
