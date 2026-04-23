#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
from rich import print

# --- Koha instellingen ---
KOHA_BASE = "http://bib-intra.marxisme.be/api/v1"  # vul je Koha server URL in
USERNAME = "kohaadmin"
PASSWORD = "Trotsky1917lenin!"

# --- 1. Haal bestaand item op ---
item_id_to_copy = 2
biblio_id_target = 2  # het bibliografische record waar het nieuwe item bij moet

url_get = f"{KOHA_BASE}/items/{item_id_to_copy}"
resp = requests.get(url_get, auth=HTTPBasicAuth(USERNAME, PASSWORD))
if resp.status_code != 200:
    print(f"Fout bij ophalen item {item_id_to_copy}: {resp.status_code}")
    print(resp.text)
    exit(1)

item_data = resp.json()
print("[bold green]Bestaand item opgehaald:[/bold green]")
print(item_data)

# --- 2. Prepareer nieuwe item data ---
new_item_data = {
    "biblio_id": biblio_id_target,
    "item_type_id": item_data.get("item_type_id"),
    "home_library_id": item_data.get("home_library_id"),
    "holding_library_id": item_data.get("holding_library_id"),
    "call_number_sort": item_data.get("call_number_sort"),
    "call_number_source": item_data.get("call_number_source"),
    "bookable": item_data.get("bookable", False),
    "replacement_price_date": item_data.get("replacement_price_date")
}

# --- 3. POST nieuw item ---
url_post = f"{KOHA_BASE}/items"
resp_post = requests.post(url_post, json=new_item_data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

print("[bold blue]Status:[/bold blue]", resp_post.status_code)
print("[bold blue]Response:[/bold blue]")
print(resp_post.json())
