# IABANK Terraform Variables
# T086 DR Pilot Light Variables

variable "environment" {
  description = "Environment name (prod, staging, dev)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "Environment must be one of: prod, staging, dev."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "iabank"
}

variable "primary_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "dr_region" {
  description = "Disaster Recovery AWS region"
  type        = string
  default     = "us-west-2"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "iabank"
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "iabank"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"

  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "DB instance class must start with 'db.'."
  }
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "DB allocated storage must be between 20 and 1000 GB."
  }
}

variable "backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_period >= 1 && var.backup_retention_period <= 35
    error_message = "Backup retention period must be between 1 and 35 days."
  }
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health/"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "iabank.com"
}

variable "api_subdomain" {
  description = "API subdomain"
  type        = string
  default     = "api"
}

variable "monitoring_interval" {
  description = "Enhanced monitoring interval in seconds"
  type        = number
  default     = 60

  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.monitoring_interval)
    error_message = "Monitoring interval must be one of: 0, 1, 5, 10, 15, 30, 60."
  }
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = true
}

variable "health_check_failure_threshold" {
  description = "Number of consecutive failures before marking unhealthy"
  type        = number
  default     = 3

  validation {
    condition     = var.health_check_failure_threshold >= 1 && var.health_check_failure_threshold <= 10
    error_message = "Health check failure threshold must be between 1 and 10."
  }
}

variable "health_check_request_interval" {
  description = "Health check request interval in seconds"
  type        = number
  default     = 30

  validation {
    condition     = contains([10, 30], var.health_check_request_interval)
    error_message = "Health check request interval must be either 10 or 30 seconds."
  }
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "IABANK"
    Environment = "production"
    Purpose     = "DR-Pilot-Light"
    Compliance  = "T086"
  }
}