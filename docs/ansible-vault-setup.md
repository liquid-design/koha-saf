# Ansible Vault setup

`inventory/group_vars/all/vault.yml` wordt versleuteld met Ansible Vault. De vault is **vereist** voor `playbooks/10-flask-isbn.yml` (Basic Auth voor de scan-app) en valt zonder vault-wachtwoord meteen om.

`ansible.cfg` regel 9 verwijst naar `~/.ansible-vault-pass-koha-saf`. Zolang dat bestand bestaat hoeft geen enkel playbook-commando een extra flag mee te krijgen.

---

## Eenmalige setup

```bash
# Genereer een sterk vault password en bewaar het buiten de repo
openssl rand -base64 32 > ~/.ansible-vault-pass-koha-saf
chmod 600 ~/.ansible-vault-pass-koha-saf
```

`ansible.cfg` bevat al:

```ini
[defaults]
vault_password_file = ~/.ansible-vault-pass-koha-saf
```

Dus na de bovenstaande twee commando's werkt de vault automatisch.

> ⚠️ `~/.ansible-vault-pass-koha-saf` mag **nooit** in git komen. Controleer:
> ```bash
> git check-ignore -v ~/.ansible-vault-pass-koha-saf || \
>   echo "WAARSCHUWING: password file is NIET ignored — fix .gitignore"
> ```

---

## Inhoud van de vault

De vault bevat momenteel twee variabelen, allebei voor `flask_isbn_app`:

```yaml
# Basic Auth voor scan.marxisme.be / scan-test.marxisme.be
vault_flask_htpasswd_user: "saf"
vault_flask_htpasswd_hash: "saf:$2y$05$abcdefghijklmnopqrstuv..."
```

| Variabele | Geconsumeerd in | Doel |
|-----------|------------------|------|
| `vault_flask_htpasswd_user` | `roles/flask_isbn_app/defaults/main.yml` regel 28 | Apache Basic Auth username |
| `vault_flask_htpasswd_hash` | `roles/flask_isbn_app/defaults/main.yml` regel 29 | Volledige htpasswd-regel (`user:hash`) |

> ℹ️ De hash genereer je **offline**, niet via Ansible. We gebruiken bewust geen `community.general.htpasswd` module — die zou platte tekst in vars vereisen. Door alleen de hash op te slaan blijft het klaartekst-wachtwoord nergens buiten de offline `htpasswd` aanroep.

---

## Hash genereren

```bash
htpasswd -nbB saf 'echt-wachtwoord-hier'
# Output: saf:$2y$05$abc...
```

Die complete output-regel (inclusief de `saf:` prefix) komt in `vault_flask_htpasswd_hash`.

Roteren is hetzelfde: nieuwe hash genereren, vault editen, playbook 10 opnieuw draaien.

---

## Vault file aanmaken (eerste keer)

```bash
cd koha-saf/ansible
ansible-vault create inventory/group_vars/all/vault.yml
```

Editor opent. Voer in:

```yaml
vault_flask_htpasswd_user: "saf"
vault_flask_htpasswd_hash: "saf:$2y$05$..."
```

Sla op en verlaat editor.

---

## Vault file aanpassen

```bash
ansible-vault edit inventory/group_vars/all/vault.yml
```

---

## Vault file bekijken zonder editen

```bash
ansible-vault view inventory/group_vars/all/vault.yml
```

---

## Vault-wachtwoord roteren

Verstandig om jaarlijks te doen:

```bash
ansible-vault rekey inventory/group_vars/all/vault.yml
```

Daarna een nieuw `~/.ansible-vault-pass-koha-saf` genereren met de nieuwe waarde.

---

## Deploy zonder de password file (bv. in CI)

```bash
ansible-playbook -i inventory/terraform.py \
  playbooks/10-flask-isbn.yml \
  --vault-password-file ~/.ansible-vault-pass-koha-saf
```

Of via environment variabele:

```bash
export ANSIBLE_VAULT_PASSWORD_FILE=~/.ansible-vault-pass-koha-saf
ansible-playbook -i inventory/terraform.py playbooks/10-flask-isbn.yml
```

---

## Wat de vault niet bevat (nog)

Bij toekomstige uitbreidingen horen deze vars logisch in de vault, maar er is op dit moment geen role die ze consumeert. **Voeg ze pas toe wanneer de bijhorende role bestaat**, anders heb je dode vars in de vault.

| Toekomstige var | Wanneer relevant |
|------------------|-------------------|
| `vault_koha_smtp_pass_prod` / `vault_koha_smtp_pass_test` | Wanneer `koha_business_smtp` bestaat (zie doc 08 §8.1) |
| `vault_b2_application_key_id` / `vault_b2_application_key` | Wanneer `koha_backup` role bestaat |
| `vault_koha_staff_password_hashes` | Wanneer hardcoded hashes in `koha_business_staff/defaults/main.yml` verplaatst worden |
