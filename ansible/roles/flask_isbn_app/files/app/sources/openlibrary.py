"""
Open Library bron.

Endpoint:  https://openlibrary.org/api/books
Query:     ?bibkeys=ISBN:<ISBN>&format=json&jscmd=data
Schema:    JSON

Crowdsourced via Internet Archive. Voor obscure of recent uitgegeven
Vlaamse non-fictie zelden bruikbaar, maar laatste fallback in de keten.
"""

import requests
from .base import Source, BookRecord, extract_year


class OpenLibrarySource(Source):
    name = "OpenLibrary"
    timeout = 5

    def _fetch(self, isbn: str, rec: BookRecord) -> None:
        url = (
            "https://openlibrary.org/api/books"
            f"?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        key = f"ISBN:{isbn}"
        if key not in data:
            return
        book = data[key] or {}

        rec.title = book.get("title")
        rec.subtitle = book.get("subtitle")
        rec.authors = [a.get("name", "") for a in book.get("authors", []) if a.get("name")]

        publishers = book.get("publishers", []) or []
        rec.publishers = [p.get("name") for p in publishers if p.get("name")]

        # OpenLibrary heeft publish_places als aparte structuur
        places = book.get("publish_places", []) or []
        if places:
            rec.publish_place = places[0].get("name")

        rec.publish_date = extract_year(book.get("publish_date"))
        rec.pagecount = book.get("number_of_pages")

        # Subjects: kunnen dicts {name, url} of strings zijn
        subjects = book.get("subjects", []) or []
        for s in subjects:
            name = s.get("name") if isinstance(s, dict) else str(s)
            if name and name not in rec.categories:
                rec.categories.append(name)

        # Cover
        cover = book.get("cover", {}) or {}
        rec.cover = cover.get("large") or cover.get("medium") or cover.get("small")

        # Notes / descriptions
        notes = book.get("notes")
        if isinstance(notes, dict):
            rec.description = notes.get("value")
        elif isinstance(notes, str):
            rec.description = notes

        rec.found = not rec.is_empty()
