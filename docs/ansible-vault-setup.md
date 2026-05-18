# Ansible Vault setup voor SMTP-wachtwoorden

## Eenmalige setup

Als je nog geen Ansible Vault gebruikt:

```bash
cd ~/Documents/koha-saf/ansible

# Genereer een sterke vault password en bewaar 'm veilig
# (niet in git, niet in cleartext op disk in repo)
openssl rand -base64 32 > ~/.ansible-vault-pass-koha-saf
chmod 600 ~/.ansible-vault-pass-koha-saf

# Vertel Ansible waar de password file staat
# Optie A: via ansible.cfg
cat >> ansible.cfg << 'EOF'
[defaults]
vault_password_file = ~/.ansible-vault-pass-koha-saf
EOF

# Optie B: via env var (handig in CI)
# export ANSIBLE_VAULT_PASSWORD_FILE=~/.ansible-vault-pass-koha-saf
```

## Vault file aanmaken

```bash
cd ~/Documents/koha-saf/ansible
ansible-vault create inventory/group_vars/all/vault.yml
```

Editor opent. Voer in:

```yaml
# SMTP credentials voor mail.socialisme.be
vault_koha_smtp_pass_test: "WACHTWOORD-VAN-saf-test@marxisme.be"
vault_koha_smtp_pass_prod: "WACHTWOORD-VAN-saf@marxisme.be"
```

Sla op en verlaat editor.

## Vault file aanpassen later

```bash
ansible-vault edit inventory/group_vars/all/vault.yml
```

## Vault file bekijken zonder editen

```bash
ansible-vault view inventory/group_vars/all/vault.yml
```

## Vault password roteren (verstandig om jaarlijks te doen)

```bash
ansible-vault rekey inventory/group_vars/all/vault.yml
```

## Belangrijke gitignore

`~/.ansible-vault-pass-koha-saf` mag NOOIT in git komen. Verifieer:

```bash
cd ~/Documents/koha-saf/ansible
# Test of git hem ziet
git check-ignore -v ../.ansible-vault-pass-koha-saf || \
  echo "WAARSCHUWING: password file is NIET ignored — check .gitignore"
```

Als je die WAARSCHUWING ziet, voeg toe:

```bash
echo ".ansible-vault-pass-koha-saf" >> ~/.gitignore_global
# of als je ~/.ansible-vault-pass-koha-saf in repo root staat:
echo "/.ansible-vault-pass*" >> .gitignore
```

## Deploy met vault

Geen extra flag nodig als ansible.cfg de vault_password_file kent.
Anders:

```bash
ansible-playbook -i inventory/terraform.py -l test \
  playbooks/07-koha-business.yml \
  --vault-password-file ~/.ansible-vault-pass-koha-saf
```
