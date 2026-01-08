#!/usr/bin/env python3
import json
import subprocess
import sys

def terraform_output():
    try:
        result = subprocess.check_output(
            ["terraform", "output", "-json"],
            cwd="../terraform"
        )
        return json.loads(result)
    except subprocess.CalledProcessError:
        sys.exit("Error: terraform output failed")

def main():
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
        inventory["all"]["hosts"].append(host)

        inventory["_meta"]["hostvars"][host] = {
            "ansible_host": d["ip"],
            "do_region": d["region"],
            "do_tags": d["tags"],
        }

        if "test" in d["tags"]:
            inventory["test"]["hosts"].append(host)
        else:
            inventory["prod"]["hosts"].append(host)

    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
