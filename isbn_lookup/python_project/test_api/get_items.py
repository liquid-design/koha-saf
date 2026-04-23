import requests
from requests.auth import HTTPBasicAuth

KOHA_BASE = "http://bib-intra.marxisme.be/api/v1"
USERNAME = "kohaadmin"
PASSWORD = "Trotsky1917lenin!"

biblio_id = 24
url = f"{KOHA_BASE}/biblios/{biblio_id}/items"

resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))

print("Status:", resp.status_code)
print("JSON:", resp.json())
