variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "custom_postgres_image_repo" { type = string }

module "postgres" {
  source                = "./modules/postgres"
  environment            = var.environment
  vpc_id                 = var.vpc_id
  subnet_ids             = var.subnet_ids
  custom_image_repo      = var.custom_postgres_image_repo
  instance_class         = var.environment == "prod" ? "db.r6g.xlarge" : "db.t4g.large"
  allocated_storage_gb   = var.environment == "prod" ? 500 : 100
}

module "redis" {
  source      = "./modules/redis"
  environment = var.environment
  vpc_id      = var.vpc_id
  subnet_ids  = var.subnet_ids
  node_type   = var.environment == "prod" ? "cache.r6g.large" : "cache.t4g.small"
}

module "storage" {
  source      = "./modules/storage"
  environment = var.environment
}

module "opensearch" {
  source      = "./modules/opensearch"
  environment = var.environment
  vpc_id      = var.vpc_id
  subnet_ids  = var.subnet_ids
}

output "postgres_private_ip" { value = module.postgres.postgres_private_ip }
output "redis_primary_endpoint" { value = module.redis.redis_primary_endpoint }
output "opensearch_endpoint" { value = module.opensearch.opensearch_endpoint }
output "uploads_bucket" { value = module.storage.uploads_bucket }
