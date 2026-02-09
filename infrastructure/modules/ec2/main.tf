# EC2 Instance
resource "aws_instance" "main" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = var.security_group_ids
  iam_instance_profile   = var.iam_instance_profile

  # User data script for initialization
  user_data = var.user_data

  # Key pair for SSH access (optional)
  key_name = var.key_pair_name

  # Root volume
  root_block_device {
    volume_type           = "gp2"
    volume_size           = 20
    delete_on_termination = true
    encrypted             = true
  }

  # Additional volume for logs and data
  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_type           = "gp2"
    volume_size           = 30
    delete_on_termination = true
    encrypted             = true
  }

  tags = {
    Name = "${var.project_name}-ec2-${var.environment}"
  }

  # Ensure proper shutdown behavior
  disable_api_termination = false
  instance_initiated_shutdown_behavior = "terminate"
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
