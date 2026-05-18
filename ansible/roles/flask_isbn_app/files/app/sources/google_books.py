"""
Google Books bron.

Endpoint:  https://www.googleapis.com/books/v1/volumes
Query:     ?q=isbn:<ISBN>
Schema:    JSON

Goede dekking voor commerciële (Engels/Nederlands) titels.
Kan rate-limited zijn bij parallelle calls zonder API-key — daarom
worden bronnen sequentieel ondervraagd in de routes, niet parallel.
"""

import requests
from .base import Source, BookRecord, extract_year, normalize_language


class GoogleBooksSource(Source):
    name = "Google Books"
    timeout = 5

    def _fetch(self, isbn: str, rec: BookRecord) -> None:
        url = (
            "https://www.googleapis.com/books/v1/volumes"
            f"?q=isbn:{isbn}&maxResults=1"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("totalItems", 0) == 0 or "items" not in data:
            return

        vi = data["items"][0].get("volumeInfo", {}) or {}

        rec.title = vi.get("title")
        rec.subtitle = vi.get("subtitle")
        rec.authors = vi.get("authors", []) or []

        if vi.get("publisher"):
            rec.publishers = [vi["publisher"]]

        rec.publish_date = extract_year(vi.get("publishedDate"))
        rec.pagecount = vi.get("pageCount")
        rec.description = vi.get("description")
        rec.categories = vi.get("categories", []) or []
        rec.language = normalize_language(vi.get("language"))

        links = vi.get("imageLinks", {}) or {}
        rec.cover = links.get("thumbnail") or links.get("smallThumbnail")

        rec.found = not rec.is_empty()
