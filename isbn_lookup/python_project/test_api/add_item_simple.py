import requests
from requests.auth import HTTPBasicAuth

KOHA_BASE = "http://bib-intra.marxisme.be/api/v1"
USERNAME = "kohaadmin"
PASSWORD = "Trotsky1917lenin!"

biblio_id = 2
url = f"{KOHA_BASE}/biblios/{biblio_id}/items"

payload = {
    "home_library_id": "CPL",
    "holding_library_id": "CPL",
    "item_type_id": "BK",
    "not_for_loan_status": 0,
    "lost_status": 0,
    "withdrawn": 0
}

resp = requests.post(
    url,
    json=payload,
    auth=HTTPBasicAuth(USERNAME, PASSWORD)
)

print("Status:", resp.status_code)
try:
    print("Response:", resp.json())
except:
    print("RAW:", resp.text)
