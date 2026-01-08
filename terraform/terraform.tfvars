#do_token = "dop_v1_b84b21fb5f12f407cd996d832984da7a926282fc3c35ad2d83010806d2dc9278"
# terraform-cloud/terraform.tfvars
# include = "~/vaults/terraform/secrets.tfvars"

droplets = {
  "koha-saf-prod" = {
    name   = "bib.marxisme.be"
    region = "ams3"
    size   = "s-2vcpu-2gb"
    image  = "debian-12-x64"
    tags      = ["koha", "prod"]
    user_data = <<-EOF
    #cloud-config
    packages:
      - htop
      - git
    users:
      - name: ansible
        sudo: ALL=(ALL) NOPASSWD:ALL
        shell: /bin/bash
        lock_passwd: false
        passwd: "$6$DpwMNhLPWjS.EhFW$uJpKn.ph3f4msYQga94aZPjHK3xtn/gpBskyTnWSJGnxQsCzwTfJ8gXwFjuf.csa3MrQbFAuQs4vM71ZDGMvd."
        ssh_authorized_keys:
          - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA5Scs7UK9JsGYK8Q+Ib/gY71A6Z4HcVG1Nu2AyG/Pv4 ansible-infra
          - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAKMdO3JrvmB4g/YTD9yXEq09LhySJ5itMvliMVhq1RS sander@liquid-design.be
  EOF
  }


  "koha-saf-test" = {
    name   = "bib-test.marxisme.be"
    region = "ams3"
    size   = "s-2vcpu-2gb"
    image  = "debian-12-x64"
    tags      = ["koha", "test"]
    user_data = <<-EOF
    #cloud-config
    packages:
      - htop
      - git
    users:
      - name: ansible
        sudo: ALL=(ALL) NOPASSWD:ALL
        shell: /bin/bash
        lock_passwd: false
        passwd: "$6$DpwMNhLPWjS.EhFW$uJpKn.ph3f4msYQga94aZPjHK3xtn/gpBskyTnWSJGnxQsCzwTfJ8gXwFjuf.csa3MrQbFAuQs4vM71ZDGMvd."
        ssh_authorized_keys:
          - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA5Scs7UK9JsGYK8Q+Ib/gY71A6Z4HcVG1Nu2AyG/Pv4 ansible-infra
          - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAKMdO3JrvmB4g/YTD9yXEq09LhySJ5itMvliMVhq1RS sander@liquid-design.be
  EOF
  }
}
