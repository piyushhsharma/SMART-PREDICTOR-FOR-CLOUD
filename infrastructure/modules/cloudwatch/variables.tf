variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "log_groups" {
  description = "List of log groups to create"
  type = list(object({
    name          = string
    retention_days = number
  }))
}

variable "instance_id" {
  description = "EC2 instance ID for metrics"
  type        = string
  default     = ""
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  type        = string
  default     = ""
}

variable "alarm_thresholds" {
  description = "Thresholds for CloudWatch alarms"
  type = object({
    cpu_utilization_high = number
    memory_utilization_high = number
    disk_utilization_high = number
  })
  default = {
    cpu_utilization_high    = 80
    memory_utilization_high = 85
    disk_utilization_high   = 90
  }
}
