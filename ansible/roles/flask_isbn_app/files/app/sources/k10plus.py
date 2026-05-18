"""
K10plus SRU bron - Duitse PICA verbundcatalogus (GBV + BSZ).

Endpoint:  http://sru.k10plus.de/opac-de-627
Query:     pica.isb=<ISBN>
Schema:    marcxml (we vragen MARC21 op ipv PICA-XML voor consistentie)

Goede dekking voor academisch materiaal, óók veel Nederlandstalige titels
omdat UvA, UGent en andere universiteiten via OCLC/PICA aanleveren.
Auteursveld komt al in MARC 100$a-formaat 'Achternaam, Voornaam', direct
bruikbaar voor Koha.
"""

import requests
import xml.etree.ElementTree as ET
from .base import Source, BookRecord, extract_year

_NS = {
    "zs": "http://www.loc.gov/zing/srw/",
    "marc": "http://www.loc.gov/MARC21/slim",
}


def _sf(field, code):
    """Subfield helper: vind eerste <subfield code='X'> in een datafield."""
    el = field.find(f"marc:subfield[@code='{code}']", _NS)
    return el.text.strip() if el is not None and el.text else None


class K10plusSource(Source):
    name = "K10plus"
    timeout = 7

    def _fetch(self, isbn: str, rec: BookRecord) -> None:
        url = (
            "http://sru.k10plus.de/opac-de-627"
            "?version=1.1&operation=searchRetrieve"
            f"&query=pica.isb={isbn}"
            "&maximumRecords=1"
            "&recordSchema=marcxml"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        nrec = root.findtext("zs:numberOfRecords", default="0", namespaces=_NS)
        if nrec == "0":
            return

        # Loop alle MARC datafields en vul rec op basis van tag
        for f in root.findall(".//marc:datafield", _NS):
            tag = f.attrib.get("tag")

            if tag == "245":  # titel
                rec.title = _sf(f, "a") or rec.title
                rec.subtitle = _sf(f, "b") or rec.subtitle
                # Strip trailing punctuatie die MARC-conventie meedraagt
                if rec.title:
                    rec.title = rec.title.rstrip(" /:")
                if rec.subtitle:
                    rec.subtitle = rec.subtitle.rstrip(" /:")

            elif tag == "100":  # hoofdauteur
                name = _sf(f, "a")
                if name and name.rstrip(",.") not in rec.authors:
                    rec.authors.append(name.rstrip(",."))

            elif tag == "700":  # mede-auteurs
                name = _sf(f, "a")
                if name and name.rstrip(",.") not in rec.authors:
                    rec.authors.append(name.rstrip(",."))

            elif tag in ("260", "264"):  # publicatie (264 = MARC21 modern)
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

            elif tag == "300":  # paginas
                pages = _sf(f, "a")
                if pages:
                    import re
                    m = re.search(r"(\d+)", pages)
                    if m:
                        rec.pagecount = int(m.group(1))

            elif tag == "041":  # taal
                lang = _sf(f, "a")
                if lang and not rec.language:
                    rec.language = lang.lower()

            elif tag in ("650", "689"):  # onderwerpen
                subj = _sf(f, "a")
                if subj and subj not in rec.categories:
                    rec.categories.append(subj)

            elif tag == "520":  # samenvatting
                desc = _sf(f, "a")
                if desc and not rec.description:
                    rec.description = desc

        rec.found = not rec.is_empty()
