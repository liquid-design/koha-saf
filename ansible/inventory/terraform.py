#!/usr/bin/env python3
"""
Dynamic Ansible inventory voor Koha SAF op basis van Terraform state.

Toegevoegde waarde voor dit project:
- Verwijdert handmatige inventory-bestanden
- Garandeert dat Ansible exact dezelfde infrastructuur ziet
  als Terraform heeft uitgerold
- Maakt duidelijke scheiding tussen 'prod' en 'test' omgevingen
  op basis van DigitalOcean tags

Dit script wordt typisch aangeroepen door Ansible met:
  ansible-inventory -i inventory.py --list
"""

import json
import subprocess
import sys

def terraform_output():
    """
    Haalt de actuele Terraform outputs op in JSON-formaat.

    Context binnen Koha SAF:
    - Terraform is de single source of truth voor infrastructuur
    - Droplet namen, IP-adressen, regio en tags worden daar beheerd
    - Ansible consumeert deze data indirect via dit script

    Verwachting:
    - Terraform is al uitgevoerd (apply)
    - De terraform directory bevat een geldige state

    Foutafhandeling:
    - Bij falen stoppen we hard, omdat Ansible zonder inventory
      niet veilig kan draaien
    """
    try:
        result = subprocess.check_output(
            ["terraform", "output", "-json"],
            cwd="../terraform"
        )
        return json.loads(result)
    except subprocess.CalledProcessError:
        sys.exit("Error: terraform output failed")

def main():
    """
    Bouwt een Ansible inventory structuur op basis van Terraform output.

    Resultaat:
    - Volledig dynamische inventory in Ansible JSON-formaat
    - Geen statische hosts-bestanden nodig
    - Automatische groepering in 'prod' en 'test'

    Architecturale keuze:
    - Omgevingen worden bepaald door DigitalOcean tags
    - Geen environment-logica hardcoded in Ansible zelf
    """

    data = terraform_output()
    droplets = data["droplets"]["value"]

    inventory = {
        "_meta": {"hostvars": {}},
        "all": {"hosts": []},
        "prod": {"hosts": []},
        "test": {"hosts": []},
    }

    for key, d in droplets.items():
        host = d["name"]
        
        # Alle hosts komen altijd in de 'all' groep
        inventory["all"]["hosts"].append(host)


        # Host-specifieke variabelen
        # Deze worden later door rollen gebruikt zonder
        # expliciete inventory-bestanden
        inventory["_meta"]["hostvars"][host] = {
            "ansible_host": d["ip"],        # Publiek IP-adres van de droplet
            "do_region": d["region"],       # DigitalOcean regio (context / logging)
            "do_tags": d["tags"],           # Tags bepalen omgeving (prod/test)
        }

        # Environment-indeling op basis van tags
        # Dit maakt het mogelijk om:
        #   ansible-playbook -l test ...
        #   ansible-playbook -l prod ...
        # te draaien zonder extra configuratie
        if "test" in d["tags"]:
            inventory["test"]["hosts"].append(host)
        else:
            inventory["prod"]["hosts"].append(host)


    # Ansible verwacht JSON output op stdout
    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
