# koha-saf

## Git
clone eerst de repo op je machine
wijzig voor terraform/terraform.tfvars de ssh keys van je huidige host 
Daarna genereer een key voor de ansible user op je machine 
Verzin een wachtwoord voor je ansible user en hash dat met SHA512
Zet deze in je terraform/terraform.tfvars


## terraform
Installeer terraform op je mac met brew install terraform
Om terraform op te zetten moet je eerst de provider installeren

cd koha-saf/terraform
sudo terraform init

sudo terraform plan \
   -var-file=terraform.tfvars \
   -var-file=secrets/secrets.tfvars

sudo terraform apply \
   -var-file=terraform.tfvars \
   -var-file=secrets/secrets.tfvars


## ansible
maak aan nopass ansible user aan 
ssh-keygen -t ed25519 -f ~/.ssh/ansible_nopass -N ""
zet de ansible_nopass.pub in je terraform.tfvars

Er word gebruik gemaakt van dynamic inventory door ansible/inventroy/terraform.py
ansible-inventory --list
