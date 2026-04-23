import requests
from requests.auth import HTTPBasicAuth

# Basisinstellingen
KOHA_BASE = "http://bib-intra.marxisme.be/api/v1"  # vul je Koha server URL in
USERNAME = "kohaadmin"                              # jouw API gebruiker
PASSWORD = "Trotsky1917lenin!"                        # jouw wachtwoord

# Test endpoint: libraries ophalen
url = f"{KOHA_BASE}/libraries"

# Verstuur GET request met Basic Auth
resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))

# Resultaat tonen
print("Status code:", resp.status_code)
print("Response:", resp.text)
