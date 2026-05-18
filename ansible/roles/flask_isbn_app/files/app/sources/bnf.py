"""
BnF SRU bron - Bibliotheque nationale de France.

Endpoint:  http://catalogue.bnf.fr/api/SRU
Query:     bib.isbn any "<ISBN>"
Schema:    UNIMARC (BnF's eigen variant, geen recordSchema parameter)

Quirks (zie userMemories):
- recordSchema=unimarcXchange parameter NIET meegeven (geeft ExplainResponse)
- 200$a = titel, 200$e = echte ondertitel (200$b = General Material Designation)
- 200$b is GEEN ondertitel, dus negeren
- 608 = Form/Genre (geen onderwerp)
- Dates kunnen "DL 2019" prefix hebben
- Place names kunnen tussen [haakjes]
"""

import requests
import urllib.parse
import xml.etree.ElementTree as ET
from .base import Source, BookRecord, extract_year

_NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "mxc": "info:lc/xmlns/marcxchange-v2",
}


def _sf(field, code):
    el = field.find(f"mxc:subfield[@code='{code}']", _NS)
    return el.text.strip() if el is not None and el.text else None


class BnfSource(Source):
    name = "BnF"
    timeout = 8

    def _fetch(self, isbn: str, rec: BookRecord) -> None:
        q = f'bib.isbn any "{isbn}"'
        url = (
            "http://catalogue.bnf.fr/api/SRU"
            "?version=1.2&operation=searchRetrieve"
            f"&query={urllib.parse.quote(q)}"
            "&maximumRecords=1"
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        nrec = root.findtext("srw:numberOfRecords", default="0", namespaces=_NS)
        if nrec == "0":
            return

        for f in root.findall(".//mxc:datafield", _NS):
            tag = f.attrib.get("tag")

            if tag == "200":  # UNIMARC titel
                # $a = titel; $e = echte ondertitel; $b NEGEREN (GMD)
                rec.title = _sf(f, "a") or rec.title
                rec.subtitle = _sf(f, "e") or rec.subtitle
                # Author of statement of responsibility in $f
                resp_stat = _sf(f, "f")
                if resp_stat and not rec.authors:
                    # Tijdelijke parsing; 700-veld geeft cleanere data
                    rec.authors.append(resp_stat)
                if rec.title:
                    rec.title = rec.title.rstrip(" /:")
                if rec.subtitle:
                    rec.subtitle = rec.subtitle.rstrip(" /:")

            elif tag in ("700", "701", "702"):  # auteurs
                # $a = achternaam, $b = voornaam
                last = _sf(f, "a") or ""
                first = _sf(f, "b") or ""
                if last or first:
                    name = f"{last}, {first}".strip(", ")
                    if name and name not in rec.authors:
                        # Vervang voorlopige author uit 200$f indien aanwezig
                        if len(rec.authors) == 1 and "," not in rec.authors[0]:
                            rec.authors = [name]
                        else:
                            rec.authors.append(name)

            elif tag == "210":  # publicatie (UNIMARC oud)
                place = _sf(f, "a")
                pub = _sf(f, "c")
                date = _sf(f, "d")
                if place and not rec.publish_place:
                    rec.publish_place = place.strip("[]").rstrip(" :;,")
                if pub:
                    pub_clean = pub.rstrip(" ,")
                    if pub_clean and pub_clean not in rec.publishers:
                        rec.publishers.append(pub_clean)
                if date and not rec.publish_date:
                    rec.publish_date = extract_year(date)

            elif tag == "214":  # publicatie (UNIMARC nieuw)
                place = _sf(f, "a")
                pub = _sf(f, "c")
                date = _sf(f, "d")
                if place and not rec.publish_place:
                    rec.publish_place = place.strip("[]").rstrip(" :;,")
                if pub:
                    pub_clean = pub.rstrip(" ,")
                    if pub_clean and pub_clean not in rec.publishers:
                        rec.publishers.append(pub_clean)
                if date and not rec.publish_date:
                    rec.publish_date = extract_year(date)

            elif tag == "215":  # fysieke beschrijving
                pages = _sf(f, "a")
                if pages:
                    import re
                    m = re.search(r"(\d+)", pages)
                    if m:
                        rec.pagecount = int(m.group(1))

            elif tag == "101":  # taal
                lang = _sf(f, "a")
                if lang and not rec.language:
                    rec.language = lang.lower()

            elif tag == "606":  # onderwerpen
                subj = _sf(f, "a")
                if subj and subj not in rec.categories:
                    rec.categories.append(subj)

            elif tag == "330":  # samenvatting (UNIMARC)
                desc = _sf(f, "a")
                if desc and not rec.description:
                    rec.description = desc

        rec.found = not rec.is_empty()
