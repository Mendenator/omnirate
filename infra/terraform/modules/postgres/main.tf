variable "environment" {
  type        = string
  description = "dev | stage | prod"
}

variable "instance_class" {
  type    = string
  default = "db.t4g.large"
}

variable "allocated_storage_gb" {
  type    = number
  default = 100
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "custom_image_repo" {
  type        = string
  description = "ECR/GHCR repo for the infra/postgres image (PostGIS + pg_jsonschema). AWS RDS can't run custom extensions, so this module targets a self-managed instance (EC2 + Docker, or EKS StatefulSet) rather than RDS."
}

# NOTE: pg_jsonschema (see infra/postgres/Dockerfile) is not on RDS's allowed
# extension list, so this cannot be `aws_db_instance`. Provisioned as an EC2
# instance running the custom image behind an internal NLB; PITR is handled by
# WAL-G continuous archiving to the `postgres_wal_archive` bucket (module.storage).
resource "aws_instance" "postgres" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_class
  subnet_id              = var.subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.postgres.id]

  root_block_device {
    volume_size = var.allocated_storage_gb
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    image_repo  = var.custom_image_repo
    environment = var.environment
  })

  tags = {
    Name        = "omnirate-postgres-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_security_group" "postgres" {
  name_prefix = "omnirate-postgres-${var.environment}-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"] # internal only
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

output "postgres_private_ip" {
  value = aws_instance.postgres.private_ip
}
