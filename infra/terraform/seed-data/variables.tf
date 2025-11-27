variable "aws_region" {
  type        = string
  description = "Região AWS usada pelos recursos de seeds."
  default     = "us-east-1"
}

variable "vault_address" {
  type        = string
  description = "Endpoint do Vault usado para o backend Transit."
  default     = "https://vault.example.com"
}

variable "environment" {
  type        = string
  description = "Ambiente alvo (dev/homolog/staging/perf/dr/prod)."

  validation {
    condition     = can(regex("^(dev|homolog|staging|perf|dr|prod)$", var.environment))
    error_message = "Environment deve ser um dos: dev, homolog, staging, perf, dr, prod."
  }
}

variable "tenant_slug" {
  type        = string
  description = "Tenant/cliente alvo (slug)."
}

variable "worm_bucket_name" {
  type        = string
  description = "Nome opcional do bucket WORM; se vazio, será gerado a partir do ambiente/tenant."
  default     = ""
}

variable "worm_retention_days" {
  type        = number
  description = "Retenção mínima do Object Lock (dias)."
  default     = 365

  validation {
    condition     = var.worm_retention_days >= 365
    error_message = "Retenção WORM deve ser >= 365 dias."
  }
}

variable "off_peak_window_utc" {
  type        = string
  description = "Janela off-peak UTC usada pelos manifestos/Argo (HH:MM-HH:MM)."
  default     = "02:00-05:00"

  validation {
    condition     = can(regex("^[0-2][0-9]:[0-5][0-9]-[0-2][0-9]:[0-5][0-9]$", var.off_peak_window_utc))
    error_message = "off_peak_window_utc deve seguir o formato HH:MM-HH:MM."
  }
}

variable "default_tags" {
  type        = map(string)
  description = "Tags padrão aplicadas a todos os recursos."
  default = {
    owner      = "seed-platform"
    managed_by = "terraform"
  }
}

variable "redis_engine_version" {
  type        = string
  description = "Versão do Redis para a fila curta."
  default     = "7.1"
}

variable "redis_node_type" {
  type        = string
  description = "Instância usada no Redis (fila curta)."
  default     = "cache.t3.micro"
}

variable "redis_num_cache_clusters" {
  type        = number
  description = "Quantidade de nós (>=2 para failover)."
  default     = 2

  validation {
    condition     = var.redis_num_cache_clusters >= 2
    error_message = "Use pelo menos 2 nós para permitir failover automático."
  }
}

variable "redis_snapshot_retention_limit" {
  type        = number
  description = "Quantos snapshots manter para rollback."
  default     = 1

  validation {
    condition     = var.redis_snapshot_retention_limit >= 1
    error_message = "Snapshot retention deve ser >= 1 para rollback."
  }
}

variable "redis_snapshot_window" {
  type        = string
  description = "Janela de snapshot (hh:mm-hh:mm UTC) alinhada ao off-peak."
  default     = "03:00-04:00"

  validation {
    condition     = can(regex("^[0-2][0-9]:[0-5][0-9]-[0-2][0-9]:[0-5][0-9]$", var.redis_snapshot_window))
    error_message = "Snapshot window deve seguir o formato HH:MM-HH:MM."
  }
}

variable "redis_maintenance_window" {
  type        = string
  description = "Janela de manutenção do Redis (downtime minimizado), formato ddd:hh:mm-ddd:hh:mm."
  default     = "sun:04:00-sun:05:00"

  validation {
    condition     = can(regex("^[a-z]{3}:[0-2][0-9]:[0-5][0-9]-[a-z]{3}:[0-2][0-9]:[0-5][0-9]$", var.redis_maintenance_window))
    error_message = "Maintenance window deve seguir o formato ddd:HH:MM-ddd:HH:MM."
  }
}

variable "redis_subnet_group_name" {
  type        = string
  description = "Subnet group do Redis."
  default     = "default"
}

variable "redis_parameter_group_name" {
  type        = string
  description = "Parameter group do Redis (capacidade de DLQ/backoff)."
  default     = "default.redis7"
}

variable "redis_auth_token" {
  type        = string
  description = "Token de autenticação do Redis (usar secret externo)."
  default     = null
  sensitive   = true
}
