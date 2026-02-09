# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "main" {
  count = length(var.log_groups)

  name              = var.log_groups[count.index].name
  retention_in_days = var.log_groups[count.index].retention_days

  tags = {
    Name        = var.log_groups[count.index].name
    Project     = var.project_name
    Environment = var.environment
  }
}

# CloudWatch Metric for CPU Utilization
resource "aws_cloudwatch_metric_alarm" "cpu_utilization" {
  alarm_name          = "${var.project_name}-cpu-utilization-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = var.alarm_thresholds.cpu_utilization_high
  alarm_description   = "This metric monitors ec2 cpu utilization"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    InstanceId = var.instance_id
  }

  tags = {
    Name        = "${var.project_name}-cpu-alarm-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# CloudWatch Metric for Memory Utilization (Custom Metric)
resource "aws_cloudwatch_metric_alarm" "memory_utilization" {
  alarm_name          = "${var.project_name}-memory-utilization-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "System/Linux"
  period              = "300"
  statistic           = "Average"
  threshold           = var.alarm_thresholds.memory_utilization_high
  alarm_description   = "This metric monitors ec2 memory utilization"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    InstanceId = var.instance_id
  }

  tags = {
    Name        = "${var.project_name}-memory-alarm-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# CloudWatch Metric for Disk Utilization
resource "aws_cloudwatch_metric_alarm" "disk_utilization" {
  alarm_name          = "${var.project_name}-disk-utilization-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DiskSpaceUtilization"
  namespace           = "System/Linux"
  period              = "300"
  statistic           = "Average"
  threshold           = var.alarm_thresholds.disk_utilization_high
  alarm_description   = "This metric monitors ec2 disk utilization"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    InstanceId = var.instance_id
    Path       = "/"
  }

  tags = {
    Name        = "${var.project_name}-disk-alarm-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}
