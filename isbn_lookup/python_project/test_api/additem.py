import requests
from requests.auth import HTTPBasicAuth

# Koha REST API instellingen
KOHA_BASE = "http://bib-intra.marxisme.be/api/v1"
USERNAME = "kohaadmin"
PASSWORD = "Trotsky1917lenin!"

# Endpoint voor items
url = f"{KOHA_BASE}/items"

# Payload voor het nieuwe item
payload = {
    "biblionumber": 2,
    "itemtype": "books",
    "homebranch": "CPL",
    "currentbranch": "CPL",
    "permanent_location": "MAIN",
    "opacvisible": "y",
    "shelving_location": "STACKS"
}

# POST request met Basic Auth
resp = requests.post(url, json=payload, auth=HTTPBasicAuth(USERNAME, PASSWORD))

# Resultaat
print("Status code:", resp.status_code)
print("Response:", resp.text)
