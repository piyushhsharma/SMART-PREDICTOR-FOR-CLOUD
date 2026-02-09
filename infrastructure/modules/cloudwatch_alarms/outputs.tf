output "anomaly_alarm_arns" {
  description = "ARNs of the anomaly detection alarms"
  value = [
    aws_cloudwatch_metric_alarm.anomaly_score_high.arn,
    aws_cloudwatch_metric_alarm.anomaly_score_medium.arn,
    aws_cloudwatch_metric_alarm.ml_service_health.arn
  ]
}
