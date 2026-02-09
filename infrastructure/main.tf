terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Smart Incident Predictor"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Purpose     = "ML-based Anomaly Detection"
    }
  }
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"
  
  project_name     = var.project_name
  environment      = var.environment
  vpc_cidr         = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  availability_zones = var.availability_zones
}

# IAM Roles and Policies
module "iam" {
  source = "./modules/iam"
  
  project_name = var.project_name
  environment  = var.environment
}

# EC2 Instance for Sample Application
module "ec2" {
  source = "./modules/ec2"
  
  project_name        = var.project_name
  environment         = var.environment
  instance_type       = var.instance_type
  ami_id              = var.ami_id
  key_pair_name       = var.key_pair_name
  subnet_id           = module.vpc.public_subnet_ids[0]
  security_group_ids  = [module.vpc.security_group_id]
  iam_instance_profile = module.iam.ec2_instance_profile_name
  
  user_data = templatefile("${path.module}/user_data.sh", {
    project_name = var.project_name
    environment  = var.environment
  })
}

# CloudWatch Log Groups
module "cloudwatch_logs" {
  source = "./modules/cloudwatch"
  
  project_name = var.project_name
  environment  = var.environment
  
  log_groups = [
    {
      name = "/aws/ec2/${var.project_name}/application"
      retention_days = 14
    },
    {
      name = "/aws/ec2/${var.project_name}/ml-service"
      retention_days = 30
    }
  ]
}

# SNS Topic for Alerts
module "sns" {
  source = "./modules/sns"
  
  project_name = var.project_name
  environment  = var.environment
  
  topic_name = "${var.project_name}-alerts"
  
  subscriptions = var.alert_emails != null ? [
    for email in var.alert_emails : {
      protocol = "email"
      endpoint = email
    }
  ] : []
}

# CloudWatch Alarms for Basic Metrics
module "cloudwatch_alarms" {
  source = "./modules/cloudwatch_alarms"
  
  project_name = var.project_name
  environment  = var.environment
  instance_id  = module.ec2.instance_id
  sns_topic_arn = module.sns.topic_arn
  
  alarm_thresholds = var.alarm_thresholds
}

# Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = module.ec2.instance_id
}

output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = module.ec2.public_ip
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = module.sns.topic_arn
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value       = module.cloudwatch_logs.log_group_names
}
