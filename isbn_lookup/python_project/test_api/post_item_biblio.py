#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
from rich import print

# --- Instellingen ---
KOHA_BASE = "http://bib-intra.marxisme.be/api/v1"
USERNAME = "kohaadmin"
PASSWORD = "Trotsky1917lenin!"

# --- Item data kopiëren van Item 2 ---
new_item_data = {
    "biblio_id": 2,               # Bibliografisch record waar het item bij hoort
    "item_type_id": "BK",          # Boek
    "home_library_id": "CPL",      # Home library
    "holding_library_id": "CPL",   # Current library
    "call_number_sort": "",         # Leeg, zoals Item 2
    "call_number_source": "ddc",   # Call number source
    "bookable": False,             # Kan niet gereserveerd worden
    "replacement_price_date": "2025-12-11"  # Datum prijs ingesteld
    # Voeg hier eventueel andere velden toe die nodig zijn zoals public_notes, internal_notes
}

# --- POST request ---
resp = requests.post(
    f"{KOHA_BASE}/items",
    auth=HTTPBasicAuth(USERNAME, PASSWORD),
    json=new_item_data
)

# --- Resultaat tonen ---
print(f"Status: {resp.status_code}")
try:
    print("Response:", resp.json())
except:
    print("Response tekst:", resp.text)
