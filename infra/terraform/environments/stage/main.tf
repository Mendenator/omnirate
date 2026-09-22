terraform {
  backend "s3" {
    bucket = "omnirate-terraform-state"
    key    = "stage/terraform.tfstate"
    region = "ap-southeast-1"
  }
}

module "omnirate" {
  source                     = "../.."
  environment                = "stage"
  vpc_id                     = var.vpc_id
  subnet_ids                 = var.subnet_ids
  custom_postgres_image_repo = var.custom_postgres_image_repo
}

variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "custom_postgres_image_repo" { type = string }

output "postgres_private_ip" { value = module.omnirate.postgres_private_ip }
output "redis_primary_endpoint" { value = module.omnirate.redis_primary_endpoint }
output "opensearch_endpoint" { value = module.omnirate.opensearch_endpoint }
