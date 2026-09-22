variable "environment" { type = string }
variable "node_type" {
  type    = string
  default = "cache.t4g.small"
}
variable "subnet_ids" { type = list(string) }
variable "vpc_id" { type = string }

resource "aws_elasticache_subnet_group" "this" {
  name       = "omnirate-redis-${var.environment}"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "redis" {
  name_prefix = "omnirate-redis-${var.environment}-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id       = "omnirate-${var.environment}"
  description                = "OmniRate cache + Arq queue (Redis 7)"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = var.node_type
  num_cache_clusters         = var.environment == "prod" ? 2 : 1
  automatic_failover_enabled = var.environment == "prod"
  subnet_group_name          = aws_elasticache_subnet_group.this.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

output "redis_primary_endpoint" {
  value = aws_elasticache_replication_group.this.primary_endpoint_address
}
