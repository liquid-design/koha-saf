terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# =====================
# VARIABLES
# =====================
variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "droplets" {
  type = map(object({
    name   : string
    region : string
    size   : string
    image  : string
    tags   : list(string)
    user_data : string
  }))
  description = "Droplets to create"
}

# =====================
# RESOURCES
# =====================
resource "digitalocean_droplet" "droplet" {
  for_each = var.droplets

  name   = each.value.name
  region = each.value.region
  size   = each.value.size
  image  = each.value.image

  ssh_keys   = []   # hier kun je later je SSH keys toevoegen
  backups    = true
  ipv6       = false
  monitoring = true
  tags       = each.value.tags

  user_data = each.value.user_data

}

# =====================
# OUTPUTS
# =====================

output "droplets" {
  value = {
    for name, droplet in digitalocean_droplet.droplet :
    name => {
      name   = droplet.name
      ip     = droplet.ipv4_address
      region = droplet.region
      tags   = droplet.tags
    }
  }
}
