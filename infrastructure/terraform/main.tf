terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Primary region
provider "aws" {
  alias      = "primary"
  region     = "us-east-1"
  access_key = "dummy"
  secret_key = "dummy"
  # Validation skips for testing without AWS credentials
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
}

# DR region
provider "aws" {
  alias      = "dr"
  region     = "us-west-2"
  access_key = "dummy"
  secret_key = "dummy"
  # Validation skips for testing without AWS credentials
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
}

# VPCs
resource "aws_vpc" "primary" {
  provider   = aws.primary
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "IABANK Primary VPC"
  }
}

resource "aws_vpc" "dr" {
  provider   = aws.dr
  cidr_block = "10.1.0.0/16"

  tags = {
    Name = "IABANK DR VPC"
  }
}

# Subnets
resource "aws_subnet" "primary_private" {
  provider          = aws.primary
  vpc_id            = aws_vpc.primary.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "IABANK Primary Private Subnet"
  }
}

resource "aws_subnet" "dr_private" {
  provider          = aws.dr
  vpc_id            = aws_vpc.dr.id
  cidr_block        = "10.1.1.0/24"
  availability_zone = "us-west-2a"

  tags = {
    Name = "IABANK DR Private Subnet"
  }
}

# DB Subnet Groups
resource "aws_db_subnet_group" "primary" {
  provider   = aws.primary
  name       = "iabank-primary-subnet-group"
  subnet_ids = [aws_subnet.primary_private.id, aws_subnet.primary_private_2.id]

  tags = {
    Name = "IABANK Primary DB subnet group"
  }
}

resource "aws_subnet" "primary_private_2" {
  provider          = aws.primary
  vpc_id            = aws_vpc.primary.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "IABANK Primary Private Subnet 2"
  }
}

resource "aws_db_subnet_group" "dr" {
  provider   = aws.dr
  name       = "iabank-dr-subnet-group"
  subnet_ids = [aws_subnet.dr_private.id, aws_subnet.dr_private_2.id]

  tags = {
    Name = "IABANK DR DB subnet group"
  }
}

resource "aws_subnet" "dr_private_2" {
  provider          = aws.dr
  vpc_id            = aws_vpc.dr.id
  cidr_block        = "10.1.2.0/24"
  availability_zone = "us-west-2b"

  tags = {
    Name = "IABANK DR Private Subnet 2"
  }
}

# Security Groups
resource "aws_security_group" "rds_primary" {
  provider = aws.primary
  name     = "iabank-rds-primary"
  vpc_id   = aws_vpc.primary.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  tags = {
    Name = "IABANK RDS Primary Security Group"
  }
}

resource "aws_security_group" "rds_dr" {
  provider = aws.dr
  name     = "iabank-rds-dr"
  vpc_id   = aws_vpc.dr.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.1.0.0/16"]
  }

  tags = {
    Name = "IABANK RDS DR Security Group"
  }
}

# RDS with read replica
resource "aws_db_instance" "primary" {
  provider               = aws.primary
  identifier             = "iabank-primary"
  engine                 = "postgres"
  engine_version         = "15.7"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_encrypted      = true

  db_name  = "iabank"
  username = "iabank"
  password = "iabank_password"

  vpc_security_group_ids = [aws_security_group.rds_primary.id]
  db_subnet_group_name   = aws_db_subnet_group.primary.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn         = aws_iam_role.rds_monitoring.arn

  tags = {
    Name = "IABANK Primary Database"
  }
}

resource "aws_db_instance" "dr_replica" {
  provider                = aws.dr
  identifier              = "iabank-dr-replica"
  replicate_source_db     = aws_db_instance.primary.identifier
  instance_class          = "db.t3.micro"

  vpc_security_group_ids = [aws_security_group.rds_dr.id]

  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn         = aws_iam_role.rds_monitoring_dr.arn

  tags = {
    Name = "IABANK DR Replica Database"
  }
}

# IAM Roles for RDS Monitoring
resource "aws_iam_role" "rds_monitoring" {
  provider = aws.primary
  name     = "iabank-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  provider   = aws.primary
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_iam_role" "rds_monitoring_dr" {
  provider = aws.dr
  name     = "iabank-rds-monitoring-role-dr"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring_dr" {
  provider   = aws.dr
  role       = aws_iam_role.rds_monitoring_dr.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Application Load Balancers
resource "aws_lb" "primary" {
  provider           = aws.primary
  name               = "iabank-primary-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_primary.id]
  subnets           = [aws_subnet.primary_public.id, aws_subnet.primary_public_2.id]

  tags = {
    Name = "IABANK Primary ALB"
  }
}

resource "aws_lb" "dr" {
  provider           = aws.dr
  name               = "iabank-dr-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_dr.id]
  subnets           = [aws_subnet.dr_public.id, aws_subnet.dr_public_2.id]

  tags = {
    Name = "IABANK DR ALB"
  }
}

# Public Subnets for ALBs
resource "aws_subnet" "primary_public" {
  provider                = aws.primary
  vpc_id                  = aws_vpc.primary.id
  cidr_block              = "10.0.10.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "IABANK Primary Public Subnet"
  }
}

resource "aws_subnet" "primary_public_2" {
  provider                = aws.primary
  vpc_id                  = aws_vpc.primary.id
  cidr_block              = "10.0.11.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "IABANK Primary Public Subnet 2"
  }
}

resource "aws_subnet" "dr_public" {
  provider                = aws.dr
  vpc_id                  = aws_vpc.dr.id
  cidr_block              = "10.1.10.0/24"
  availability_zone       = "us-west-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "IABANK DR Public Subnet"
  }
}

resource "aws_subnet" "dr_public_2" {
  provider                = aws.dr
  vpc_id                  = aws_vpc.dr.id
  cidr_block              = "10.1.11.0/24"
  availability_zone       = "us-west-2b"
  map_public_ip_on_launch = true

  tags = {
    Name = "IABANK DR Public Subnet 2"
  }
}

# Security Groups for ALBs
resource "aws_security_group" "alb_primary" {
  provider = aws.primary
  name     = "iabank-alb-primary"
  vpc_id   = aws_vpc.primary.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "IABANK ALB Primary Security Group"
  }
}

resource "aws_security_group" "alb_dr" {
  provider = aws.dr
  name     = "iabank-alb-dr"
  vpc_id   = aws_vpc.dr.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "IABANK ALB DR Security Group"
  }
}

# Route53 Zone
resource "aws_route53_zone" "main" {
  name = "iabank.com"

  tags = {
    Name = "IABANK Main Zone"
  }
}

# DNS Failover Route53
resource "aws_route53_health_check" "primary" {
  fqdn                            = "api.iabank.com"
  port                            = 443
  type                            = "HTTPS"
  resource_path                   = "/health/"
  failure_threshold               = 3
  request_interval                = 30

  tags = {
    Name = "IABANK Primary Health Check"
  }
}

resource "aws_route53_record" "primary" {
  zone_id         = aws_route53_zone.main.zone_id
  name            = "api.iabank.com"
  type            = "A"
  set_identifier  = "primary"
  health_check_id = aws_route53_health_check.primary.id

  failover_routing_policy {
    type = "PRIMARY"
  }

  alias {
    name                   = aws_lb.primary.dns_name
    zone_id                = aws_lb.primary.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "dr" {
  zone_id        = aws_route53_zone.main.zone_id
  name           = "api.iabank.com"
  type           = "A"
  set_identifier = "dr"

  failover_routing_policy {
    type = "SECONDARY"
  }

  alias {
    name                   = aws_lb.dr.dns_name
    zone_id                = aws_lb.dr.zone_id
    evaluate_target_health = true
  }
}