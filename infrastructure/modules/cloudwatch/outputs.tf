output "log_group_names" {
  description = "Names of the CloudWatch log groups"
  value       = aws_cloudwatch_log_group.main[*].name
}

output "log_group_arns" {
  description = "ARNs of the CloudWatch log groups"
  value       = aws_cloudwatch_log_group.main[*].arn
}
