"""
KB-NL SRU bron.

Endpoint:  https://jsru.kb.nl/sru/sru
Collectie: GGC (Gemeenschappelijke Geautomatiseerde Catalogus)
Schema:    Dublin Core extended (dcx)

Quirks (zie koha-docs):
- Bare ISBN als query, geen bath.isbn= prefix
- Dublin Core elementen verschijnen direct onder srw:recordData zonder wrapper
- Meerdere dc:title elementen (titel + ondertitel)
- Date-velden bevatten soms catalogus-timestamps (regex year extractie nodig)
- Publisher: "Plaats : Uitgever" formaat moet gesplitst worden
- Taal: ISO 639-3 (3-letter code)
"""

import requests
import xml.etree.ElementTree as ET
from .base import Source, BookRecord, extract_year

_NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
}


class KbNlSource(Source):
    name = "KB-NL"
    timeout = 7

    def _fetch(self, isbn: str, rec: BookRecord) -> None:
        url = (
            "https://jsru.kb.nl/sru/sru"
            "?version=1.2&operation=searchRetrieve"
            "&x-collection=GGC"
            f"&query={isbn}"
            "&maximumRecords=1"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        nrec = root.findtext("srw:numberOfRecords", default="0", namespaces=_NS)
        if nrec == "0":
            return

        rd = root.find(".//srw:recordData", _NS)
        if rd is None:
            return

        # Titels: vaak meerdere dc:title (titel + ondertitel)
        titles = [t.text for t in rd.findall(".//dc:title", _NS) if t.text]
        if titles:
            rec.title = titles[0].strip()
            if len(titles) > 1:
                rec.subtitle = titles[1].strip()

        # Auteurs uit dc:creator + dc:contributor
        for tag in ("dc:creator", "dc:contributor"):
            for el in rd.findall(f".//{tag}", _NS):
                if el.text:
                    name = el.text.strip()
                    if name and name not in rec.authors:
                        rec.authors.append(name)

        # Publisher: "Plaats : Uitgever" formaat
        publishers_raw = [p.text for p in rd.findall(".//dc:publisher", _NS) if p.text]
        for p in publishers_raw:
            if " : " in p:
                place, pub = p.split(" : ", 1)
                if not rec.publish_place:
                    rec.publish_place = place.strip()
                rec.publishers.append(pub.strip())
            else:
                rec.publishers.append(p.strip())

        # Datum: meestal jaar of catalog timestamp; extract_year vangt beide
        for d in rd.findall(".//dc:date", _NS):
            year = extract_year(d.text)
            if year:
                rec.publish_date = year
                break

        # Taal: ISO 639-3, soms in dcterms:language ipv dc:language
        for tag in ("dc:language", "dcterms:language"):
            el = rd.find(f".//{tag}", _NS)
            if el is not None and el.text:
                rec.language = el.text.strip().lower()
                break

        # Onderwerpen
        for s in rd.findall(".//dc:subject", _NS):
            if s.text:
                subj = s.text.strip()
                if subj and subj not in rec.categories:
                    rec.categories.append(subj)

        # Samenvatting
        for d in rd.findall(".//dc:description", _NS):
            if d.text and len(d.text) > 20:  # filter korte type-aanduidingen
                rec.description = d.text.strip()
                break

        # Heeft deze bron iets bruikbaars opgeleverd?
        rec.found = not rec.is_empty()
