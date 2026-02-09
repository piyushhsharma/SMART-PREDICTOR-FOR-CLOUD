# Custom CloudWatch Alarms for ML-based Anomaly Detection

# Anomaly Score High Alert
resource "aws_cloudwatch_metric_alarm" "anomaly_score_high" {
  alarm_name          = "${var.project_name}-anomaly-score-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "AnomalyRiskScore"
  namespace           = "Custom/ML"
  period              = "60"
  statistic           = "Average"
  threshold           = "70"
  treat_missing_data  = "notBreaching"
  alarm_description   = "High anomaly risk score detected"
  alarm_actions       = [var.sns_topic_arn]

  tags = {
    Name        = "${var.project_name}-anomaly-high-alarm-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Anomaly Score Medium Alert
resource "aws_cloudwatch_metric_alarm" "anomaly_score_medium" {
  alarm_name          = "${var.project_name}-anomaly-score-medium-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "AnomalyRiskScore"
  namespace           = "Custom/ML"
  period              = "60"
  statistic           = "Average"
  threshold           = "40"
  treat_missing_data  = "notBreaching"
  alarm_description   = "Medium anomaly risk score detected"
  alarm_actions       = [var.sns_topic_arn]

  tags = {
    Name        = "${var.project_name}-anomaly-medium-alarm-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# ML Service Health Check
resource "aws_cloudwatch_metric_alarm" "ml_service_health" {
  alarm_name          = "${var.project_name}-ml-service-health-${var.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MLServiceHealth"
  namespace           = "Custom/ML"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  treat_missing_data  = "breaching"
  alarm_description   = "ML service is not responding"
  alarm_actions       = [var.sns_topic_arn]

  tags = {
    Name        = "${var.project_name}-ml-health-alarm-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}
