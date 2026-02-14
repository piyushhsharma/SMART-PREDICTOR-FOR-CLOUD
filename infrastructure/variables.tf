variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "smart-incident-predictor"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a"]
}

variable "instance_type" {
  description = "EC2 instance type - optimized for t2.micro"
  type        = string
  default     = "t2.micro"
}

variable "ami_id" {
  description = "AMI ID for EC2 instance - Amazon Linux 2"
  type        = string
  default     = "ami-0c02fb55956c7d316"
}

variable "key_pair_name" {
  description = "EC2 Key Pair name for SSH access"
  type        = string
  default     = null
}

variable "alert_emails" {
  description = "List of email addresses for alert notifications"
  type        = list(string)
  default     = null
}

variable "alarm_thresholds" {
  description = "Thresholds for CloudWatch alarms (optimized for t2.micro)"
  type = object({
    cpu_utilization_high = number
    memory_utilization_high = number
    disk_utilization_high = number
  })
  default = {
    cpu_utilization_high    = 75  # Lower threshold for t2.micro
    memory_utilization_high = 80  # Conservative memory threshold
    disk_utilization_high   = 85
  }
}

variable "enable_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = false  # Save costs on t2.micro
}

variable "assign_public_ip" {
  description = "Assign public IP to instance"
  type        = bool
  default     = true
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 8  # Minimum for t2.micro
}

variable "data_volume_size" {
  description = "Data volume size in GB"
  type        = number
  default     = 10  # Small data volume for logs
}
