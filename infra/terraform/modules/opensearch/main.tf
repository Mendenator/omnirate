variable "environment" { type = string }
variable "instance_type" {
  type    = string
  default = "r6g.large.search"
}
variable "subnet_ids" { type = list(string) }
variable "vpc_id" { type = string }

# S-03 acceptance: 3 node, 1 node down -> K9 (search p95 <=150ms) still holds.
# 3 AZs so a single-AZ failure doesn't take the cluster below quorum (2/3).
resource "aws_opensearch_domain" "entities" {
  domain_name    = "omnirate-${var.environment}"
  engine_version = "OpenSearch_2.17"

  cluster_config {
    instance_type          = var.instance_type
    instance_count         = 3
    zone_awareness_enabled = true
    zone_awareness_config { availability_zone_count = 3 }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 100
  }

  vpc_options {
    subnet_ids         = slice(var.subnet_ids, 0, 3)
    security_group_ids = [aws_security_group.opensearch.id]
  }

  encrypt_at_rest { enabled = true }
  node_to_node_encryption { enabled = true }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }
}

resource "aws_security_group" "opensearch" {
  name_prefix = "omnirate-opensearch-${var.environment}-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

# Debezium (Postgres CDC) -> Kafka Connect -> this bridge -> Redis stream
# `omnirate.cdc.entities`, consumed by apps/backend/app/workers/indexer.py.
# Kafka Connect cluster itself is provisioned separately (MSK Connect); this
# module only owns the OpenSearch domain the indexer writes to.
output "opensearch_endpoint" {
  value = aws_opensearch_domain.entities.endpoint
}
