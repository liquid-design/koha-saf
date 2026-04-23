#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
from rich import print
from rich.table import Table

# --- Instellingen ---
KOHA_BASE = "http://bib-intra.marxisme.be/api/v1"  # jouw Koha server
USERNAME = "kohaadmin"
PASSWORD = "Trotsky1917lenin!"

# --- Functie om GET requests te doen ---
def get_json(endpoint):
    url = f"{KOHA_BASE}/{endpoint}"
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"[red]Fout bij GET {endpoint}: {resp.status_code}[/red]")
        try:
            print(resp.json())
        except:
            print(resp.text)
        return None

# --- 1. GET item types ---
item_types = get_json("item_types")
if item_types:
    table = Table(title="Item Types")
    table.add_column("ID")
    table.add_column("Name")
    for it in item_types:
        table.add_row(str(it.get("id")), it.get("name", ""))
    print(table)

# --- 2. GET libraries ---
libraries = get_json("libraries")
if libraries:
    table = Table(title="Libraries")
    table.add_column("Library ID")
    table.add_column("Name")
    for lib in libraries:
        table.add_row(lib.get("library_id", ""), lib.get("name", ""))
    print(table)

# --- 3. GET items ---
items = get_json("items")
if items:
    table = Table(title="Items")
    table.add_column("Item ID")
    table.add_column("Biblio ID")
    table.add_column("Item Type ID")
    table.add_column("Home Library")
    table.add_column("Holding Library")
    for item in items:
        table.add_row(
            str(item.get("item_id", "")),
            str(item.get("biblio_id", "")),
            str(item.get("item_type_id", "")),
            str(item.get("home_library_id", "")),
            str(item.get("holding_library_id", ""))
        )
    print(table)    

# --- Ophalen van specifieke items ---
item_ids = [1, 2]  # de Item IDs die we willen ophalen
for item_id in item_ids:
    item = get_json(f"items/{item_id}")
    if item:
        table = Table(title=f"Item ID {item_id}")
        table.add_column("Item ID")
        table.add_column("Biblio ID")
        table.add_column("Item Type ID")
        table.add_column("Home Library")
        table.add_column("Holding Library")
        table.add_row(
            str(item.get("item_id", "")),
            str(item.get("biblio_id", "")),
            str(item.get("item_type_id", "")),
            str(item.get("home_library_id", "")),
            str(item.get("holding_library_id", ""))
        )
        print(table)    
