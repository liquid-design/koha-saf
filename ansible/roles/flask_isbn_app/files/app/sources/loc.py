"""
LoC SRU bron - Library of Congress.

Endpoint:  http://lx2.loc.gov:210/LCDB
Query:     bath.isbn=<ISBN>
Schema:    marcxml

Voor SAF-collectie: matige dekking. Behouden voor Engelstalig
academisch materiaal en als algemene fallback.
"""

import requests
import xml.etree.ElementTree as ET
from .base import Source, BookRecord, extract_year

_NS = {
    "zs": "http://www.loc.gov/zing/srw/",
    "marc": "http://www.loc.gov/MARC21/slim",
}


def _sf(field, code):
    el = field.find(f"marc:subfield[@code='{code}']", _NS)
    return el.text.strip() if el is not None and el.text else None


class LocSource(Source):
    name = "LoC"
    timeout = 10  # LoC kan traag zijn

    def _fetch(self, isbn: str, rec: BookRecord) -> None:
        url = (
            "http://lx2.loc.gov:210/LCDB"
            "?version=1.1&operation=searchRetrieve"
            f"&query=bath.isbn={isbn}"
            "&maximumRecords=1"
            "&recordSchema=marcxml"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        nrec = root.findtext("zs:numberOfRecords", default="0", namespaces=_NS)
        if nrec == "0":
            return

        for f in root.findall(".//marc:datafield", _NS):
            tag = f.attrib.get("tag")

            if tag == "245":
                rec.title = _sf(f, "a") or rec.title
                rec.subtitle = _sf(f, "b") or rec.subtitle
                if rec.title:
                    rec.title = rec.title.rstrip(" /:")
                if rec.subtitle:
                    rec.subtitle = rec.subtitle.rstrip(" /:")

            elif tag in ("100", "700"):
                name = _sf(f, "a")
                if name and name.rstrip(",.") not in rec.authors:
                    rec.authors.append(name.rstrip(",."))

            elif tag in ("260", "264"):
                place = _sf(f, "a")
                pub = _sf(f, "b")
                date = _sf(f, "c")
                if place and not rec.publish_place:
                    rec.publish_place = place.rstrip(" :;,")
                if pub:
                    pub_clean = pub.rstrip(" ,")
                    if pub_clean and pub_clean not in rec.publishers:
                        rec.publishers.append(pub_clean)
                if date and not rec.publish_date:
                    rec.publish_date = extract_year(date)

            elif tag == "300":
                pages = _sf(f, "a")
                if pages:
                    import re
                    m = re.search(r"(\d+)", pages)
                    if m:
                        rec.pagecount = int(m.group(1))

            elif tag == "041":
                lang = _sf(f, "a")
                if lang and not rec.language:
                    rec.language = lang.lower()

            elif tag == "650":
                subj = _sf(f, "a")
                if subj and subj not in rec.categories:
                    rec.categories.append(subj)

            elif tag == "520":
                desc = _sf(f, "a")
                if desc and not rec.description:
                    rec.description = desc

        rec.found = not rec.is_empty()
