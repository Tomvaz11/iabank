# IABANK Terraform Outputs
# T086 DR Pilot Light Outputs

# Primary Region Outputs
output "primary_rds_endpoint" {
  description = "Primary RDS instance endpoint"
  value       = aws_db_instance.primary.endpoint
  sensitive   = true
}

output "primary_rds_port" {
  description = "Primary RDS instance port"
  value       = aws_db_instance.primary.port
}

output "primary_rds_id" {
  description = "Primary RDS instance identifier"
  value       = aws_db_instance.primary.id
}

output "primary_alb_dns_name" {
  description = "Primary Application Load Balancer DNS name"
  value       = aws_lb.primary.dns_name
}

output "primary_alb_zone_id" {
  description = "Primary Application Load Balancer hosted zone ID"
  value       = aws_lb.primary.zone_id
}

output "primary_vpc_id" {
  description = "Primary VPC ID"
  value       = aws_vpc.primary.id
}

# DR Region Outputs
output "dr_rds_endpoint" {
  description = "DR RDS replica endpoint"
  value       = aws_db_instance.dr_replica.endpoint
  sensitive   = true
}

output "dr_rds_port" {
  description = "DR RDS replica port"
  value       = aws_db_instance.dr_replica.port
}

output "dr_rds_id" {
  description = "DR RDS replica identifier"
  value       = aws_db_instance.dr_replica.id
}

output "dr_alb_dns_name" {
  description = "DR Application Load Balancer DNS name"
  value       = aws_lb.dr.dns_name
}

output "dr_alb_zone_id" {
  description = "DR Application Load Balancer hosted zone ID"
  value       = aws_lb.dr.zone_id
}

output "dr_vpc_id" {
  description = "DR VPC ID"
  value       = aws_vpc.dr.id
}

# Route53 Outputs
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "route53_zone_name_servers" {
  description = "Route53 hosted zone name servers"
  value       = aws_route53_zone.main.name_servers
}

output "primary_health_check_id" {
  description = "Primary health check ID"
  value       = aws_route53_health_check.primary.id
}

# DNS Records
output "api_dns_name" {
  description = "API DNS name with failover"
  value       = "${var.api_subdomain}.${var.domain_name}"
}

output "primary_dns_record_fqdn" {
  description = "Primary DNS record FQDN"
  value       = aws_route53_record.primary.fqdn
}

output "dr_dns_record_fqdn" {
  description = "DR DNS record FQDN"
  value       = aws_route53_record.dr.fqdn
}

# Security Groups
output "primary_rds_security_group_id" {
  description = "Primary RDS security group ID"
  value       = aws_security_group.rds_primary.id
}

output "dr_rds_security_group_id" {
  description = "DR RDS security group ID"
  value       = aws_security_group.rds_dr.id
}

output "primary_alb_security_group_id" {
  description = "Primary ALB security group ID"
  value       = aws_security_group.alb_primary.id
}

output "dr_alb_security_group_id" {
  description = "DR ALB security group ID"
  value       = aws_security_group.alb_dr.id
}

# Monitoring
output "primary_rds_monitoring_role_arn" {
  description = "Primary RDS monitoring role ARN"
  value       = aws_iam_role.rds_monitoring.arn
}

output "dr_rds_monitoring_role_arn" {
  description = "DR RDS monitoring role ARN"
  value       = aws_iam_role.rds_monitoring_dr.arn
}

# RTO/RPO Information
output "rto_estimate" {
  description = "Estimated Recovery Time Objective"
  value       = "< 1 hour (with automation), < 4 hours (manual)"
}

output "rpo_estimate" {
  description = "Estimated Recovery Point Objective"
  value       = "< 5 minutes (streaming replication)"
}

# Failover Information
output "failover_instructions" {
  description = "Instructions for manual failover"
  value = {
    step_1 = "Execute: aws rds promote-read-replica --db-instance-identifier iabank-dr-replica --region us-west-2"
    step_2 = "Update application configuration to point to DR region"
    step_3 = "DNS failover is automatic via Route53 health checks"
    step_4 = "Verify health endpoint: curl https://api.iabank.com/health/"
  }
}

# Connection Strings (for application configuration)
output "primary_connection_info" {
  description = "Primary database connection information"
  value = {
    host     = aws_db_instance.primary.endpoint
    port     = aws_db_instance.primary.port
    database = aws_db_instance.primary.db_name
    username = aws_db_instance.primary.username
  }
  sensitive = true
}

output "dr_connection_info" {
  description = "DR database connection information"
  value = {
    host     = aws_db_instance.dr_replica.endpoint
    port     = aws_db_instance.dr_replica.port
    database = aws_db_instance.dr_replica.db_name
    username = aws_db_instance.dr_replica.username
  }
  sensitive = true
}