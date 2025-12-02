terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.34.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = ">= 3.25.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  # Em CI usamos plano falso/fixture; pular validações de credencial/metadados evita STS em ambientes sem AWS.
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}

provider "vault" {
  address = var.vault_address
}

locals {
  service_name = "seed-data"
  name_prefix  = "${var.environment}-${local.service_name}"

  tags = merge(var.default_tags, {
    service             = local.service_name
    environment         = var.environment
    tenant              = var.tenant_slug
    data_classification = "internal"
    pii                 = "masked"
    off_peak_window_utc = var.off_peak_window_utc
  })
}

# Bucket WORM para relatórios assinados (Object Lock obrigatório)
resource "aws_kms_key" "seed_worm" {
  description             = "KMS para WORM de seeds (${var.environment}/${var.tenant_slug})"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  tags = local.tags
}

resource "aws_s3_bucket" "seed_worm" {
  bucket              = var.worm_bucket_name != "" ? var.worm_bucket_name : "${local.name_prefix}-${var.tenant_slug}-worm"
  force_destroy       = false
  object_lock_enabled = true

  tags = merge(local.tags, {
    purpose        = "seed-data-worm"
    retention_days = tostring(var.worm_retention_days)
  })
}

resource "aws_s3_bucket_public_access_block" "seed_worm" {
  bucket = aws_s3_bucket.seed_worm.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "seed_worm" {
  bucket = aws_s3_bucket.seed_worm.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "seed_worm" {
  bucket = aws_s3_bucket.seed_worm.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.seed_worm.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_object_lock_configuration" "seed_worm" {
  bucket = aws_s3_bucket.seed_worm.id
  token  = uuid()

  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.worm_retention_days
    }
  }
}

# Fila curta (Redis) para seeds com failover e snapshots para rollback
resource "aws_elasticache_replication_group" "seed_queue" {
  replication_group_id       = replace("${local.name_prefix}-${var.tenant_slug}-queue", "/[^a-z0-9-]/", "")
  description                = "Fila curta de seeds (Celery) com off-peak e rollback"
  engine                     = "redis"
  engine_version             = var.redis_engine_version
  node_type                  = var.redis_node_type
  num_cache_clusters         = var.redis_num_cache_clusters
  multi_az_enabled           = true
  automatic_failover_enabled = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token
  maintenance_window         = var.redis_maintenance_window
  snapshot_retention_limit   = var.redis_snapshot_retention_limit
  snapshot_window            = var.redis_snapshot_window
  subnet_group_name          = var.redis_subnet_group_name
  parameter_group_name       = var.redis_parameter_group_name

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(local.tags, {
    purpose = "seed-data-queue"
  })
}

# Vault Transit para mascaramento determinístico (FPE)
resource "vault_mount" "seed_transit" {
  path                      = "transit/${var.environment}/seed-data"
  type                      = "transit"
  description               = "FPE determinístico para seeds/factories (${var.environment}/${var.tenant_slug})"
  default_lease_ttl_seconds = 3600
  max_lease_ttl_seconds     = 3600
  options = {
    version = "2"
  }
}

resource "vault_transit_secret_backend_key" "seed_fpe" {
  backend               = vault_mount.seed_transit.path
  name                  = "${var.tenant_slug}-${var.environment}"
  type                  = "aes256-gcm96"
  deletion_allowed      = false
  exportable            = false
  derived               = true
  convergent_encryption = true
}

resource "vault_policy" "seed_data" {
  name   = "seed-data-${var.environment}-${var.tenant_slug}"
  policy = <<-EOT
    path "transit/${var.environment}/seed-data/keys/${var.tenant_slug}-${var.environment}" {
      capabilities = ["read"]
    }

    path "transit/${var.environment}/seed-data/encrypt/${var.tenant_slug}-${var.environment}" {
      capabilities = ["update"]
    }

    path "transit/${var.environment}/seed-data/decrypt/${var.tenant_slug}-${var.environment}" {
      capabilities = ["update"]
    }

    path "transit/${var.environment}/seed-data/rewrap/${var.tenant_slug}-${var.environment}" {
      capabilities = ["update"]
    }
  EOT
}

output "worm_bucket_name" {
  value       = aws_s3_bucket.seed_worm.bucket
  description = "Bucket WORM com Object Lock para relatórios seed_data"
}

output "worm_kms_key_arn" {
  value       = aws_kms_key.seed_worm.arn
  description = "KMS usado no bucket WORM"
}

output "seed_queue_id" {
  value       = aws_elasticache_replication_group.seed_queue.id
  description = "ID da replicação Redis usada como fila curta"
}

output "vault_transit_path" {
  value       = vault_mount.seed_transit.path
  description = "Mount Transit responsável pelo FPE determinístico"
}
