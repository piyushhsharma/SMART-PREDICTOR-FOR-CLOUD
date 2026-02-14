# EC2 Instance - Optimized for t2.micro
resource "aws_instance" "main" {
  ami                    = var.ami_id
  instance_type          = var.instance_type  # t2.micro
  subnet_id              = var.subnet_id
  vpc_security_group_ids = var.security_group_ids
  iam_instance_profile   = var.iam_instance_profile
  user_data             = var.user_data

  # t2.micro specific optimizations
  instance_initiated_shutdown_behavior = "stop"  # Preserve data
  monitoring             = var.enable_monitoring  # Disabled by default to save costs

  # Key pair for SSH access (optional)
  key_name = var.key_pair_name

  # Root volume - optimized for t2.micro
  root_block_device {
    volume_type           = "gp2"
    volume_size           = 8  # Minimum for Amazon Linux 2
    delete_on_termination = true
    encrypted             = true
    iops                 = 100  # Minimum IOPS for cost efficiency
  }

  # Additional volume for logs and data (small)
  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_type           = "gp2"
    volume_size           = 10  # Small data volume
    delete_on_termination = true
    encrypted             = true
    iops                 = 100
  }

  tags = {
    Name        = "${var.project_name}-ec2-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
    InstanceType = var.instance_type
    ManagedBy   = "Terraform"
  }

  # Ensure proper shutdown behavior
  disable_api_termination = false
}

# CloudWatch Agent installation and configuration
resource "aws_ssm_document" "cloudwatch_agent_config" {
  name          = "${var.project_name}-cloudwatch-agent-config-${var.environment}"
  document_type = "Command"

  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Configure CloudWatch agent for ${var.project_name}"
    parameters = {
      commands = {
        type = "StringList"
        description = "Commands to run"
        default = [
          "amazon-linux-extras install epel -y",
          "yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm",
          "yum install -y https://s3.amazonaws.com/amazoncloudwatch-agent-us-east-1/amazon-linux/amd64/latest/amazon-cloudwatch-agent.rpm",
          "systemctl enable amazon-cloudwatch-agent",
          "systemctl start amazon-cloudwatch-agent"
        ]
      }
      workingDirectory = {
        type = "String"
        description = "Working directory"
        default = "/tmp"
      }
      executionTimeout = {
        type = "String"
        description = "Execution timeout"
        default = "3600"
      }
    }
    runtimeConfig = {
      "aws:runShellScript" = {
        properties = {
          commands = "{{ commands }}"
          workingDirectory = "{{ workingDirectory }}"
          executionTimeout = "{{ executionTimeout }}"
        }
      }
    }
  })
}
