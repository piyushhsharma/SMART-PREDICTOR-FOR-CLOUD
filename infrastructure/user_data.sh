#!/bin/bash

# User data script for EC2 instance initialization
set -e

# Update system
yum update -y

# Install required packages
yum install -y python3 python3-pip git htop sysstat

# Install Python dependencies
pip3 install --upgrade pip
pip3 install flask boto3 scikit-learn pandas numpy psutil schedule requests

# Create application directory
mkdir -p /opt/smart-incident-predictor
cd /opt/smart-incident-predictor

# Clone or copy application code (in real scenario, this would be from Git)
# For demo purposes, we'll create the structure
mkdir -p {src/app,src/ml,src/monitoring,src/alerting,logs,data}

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent-us-east-1/amazon-linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Create CloudWatch agent configuration
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "agent": {
    "metrics_collection_interval": 30,
    "run_as_user": "cwagent"
  },
  "metrics": {
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_iowait",
          "cpu_usage_user",
          "cpu_usage_system"
        ],
        "metrics_collection_interval": 30
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 30,
        "resources": [
          "*"
        ]
      },
      "diskio": {
        "measurement": [
          "io_time"
        ],
        "metrics_collection_interval": 30,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 30
      },
      "netstat": {
        "measurement": [
          "tcp_established",
          "tcp_close_wait"
        ],
        "metrics_collection_interval": 30
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/smart-incident-predictor/logs/application.log",
            "log_group_name": "/aws/ec2/smart-incident-predictor/application",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          },
          {
            "file_path": "/opt/smart-incident-predictor/logs/ml-service.log",
            "log_group_name": "/aws/ec2/smart-incident-predictor/ml-service",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

# Create systemd service for the application
cat > /etc/systemd/system/smart-incident-predictor.service << 'EOF'
[Unit]
Description=Smart Incident Predictor Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/smart-incident-predictor
ExecStart=/usr/bin/python3 /opt/smart-incident-predictor/src/app/sample_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for ML service
cat > /etc/systemd/system/ml-anomaly-detector.service << 'EOF'
[Unit]
Description=ML Anomaly Detection Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/smart-incident-predictor
ExecStart=/usr/bin/python3 /opt/smart-incident-predictor/src/ml/anomaly_detector.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable smart-incident-predictor
systemctl enable ml-anomaly-detector

# Create log directories with proper permissions
mkdir -p /opt/smart-incident-predictor/logs
chown -R ec2-user:ec2-user /opt/smart-incident-predictor

# Start the application
systemctl start smart-incident-predictor
systemctl start ml-anomaly-detector

echo "Smart Incident Predictor setup completed successfully!"
