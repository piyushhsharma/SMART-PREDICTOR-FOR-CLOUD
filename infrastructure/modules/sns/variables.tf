variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "topic_name" {
  description = "Name of the SNS topic"
  type        = string
}

variable "subscriptions" {
  description = "List of subscriptions for the SNS topic"
  type = list(object({
    protocol = string
    endpoint = string
  }))
  default = []
}
