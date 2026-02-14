#!/bin/bash

# User data script for t2.micro optimized deployment
set -e

# Log all output
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "🚀 Starting Smart Incident Predictor setup for t2.micro"

# Update system (minimal for t2.micro)
echo "📦 Updating system packages..."
yum update -y

# Install essential packages only
echo "📦 Installing essential packages..."
yum install -y python3 python3-pip git htop sysstat wget

# Install Python dependencies (memory efficient)
echo "🐍 Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install --no-cache-dir -r /opt/smart-incident-predictor/requirements.txt

# Create application directory structure
echo "📁 Creating application directories..."
mkdir -p /opt/smart-incident-predictor/{src,logs,data,config}
cd /opt/smart-incident-predictor

# Copy application files (in production, these would be from Git/CodeDeploy)
echo "📋 Setting up application files..."
mkdir -p src/{app,ml,monitoring,alerting}

# Install CloudWatch agent (lightweight configuration)
echo "📊 Installing CloudWatch agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent-us-east-1/amazon-linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Create optimized CloudWatch agent configuration for t2.micro
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "agent": {
    "metrics_collection_interval": 60,
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
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 300,
        "resources": [
          "/"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "netstat": {
        "measurement": [
          "tcp_established"
        ],
        "metrics_collection_interval": 300
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
            "log_stream_name": "${instance_id}",
            "timezone": "UTC"
          },
          {
            "file_path": "/opt/smart-incident-predictor/logs/ml-service.log",
            "log_group_name": "/aws/ec2/smart-incident-predictor/ml-service",
            "log_stream_name": "${instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
echo "🚀 Starting CloudWatch agent..."
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

# Create systemd service for optimized application
echo "⚙️ Creating systemd services..."

# Application service
cat > /etc/systemd/system/smart-incident-predictor.service << 'EOF'
[Unit]
Description=Smart Incident Predictor API (t2.micro Optimized)
After=network.target
Wants=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/smart-incident-predictor
Environment=PYTHONPATH=/opt/smart-incident-predictor/src
Environment=ENVIRONMENT=AWS_EC2
ExecStart=/opt/smart-incident-predictor/venv/bin/python src/app/optimized_app.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Resource limits for t2.micro
MemoryLimit=512M
CPUQuota=80%

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/smart-incident-predictor/logs /opt/smart-incident-predictor/data

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=smart-incident-predictor

[Install]
WantedBy=multi-user.target
EOF

# ML Anomaly Detector service
cat > /etc/systemd/system/ml-anomaly-detector.service << 'EOF'
[Unit]
Description=ML Anomaly Detection Service (t2.micro Optimized)
After=network.target smart-incident-predictor.service
Wants=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/smart-incident-predictor
Environment=PYTHONPATH=/opt/smart-incident-predictor/src
Environment=ENVIRONMENT=AWS_EC2
ExecStart=/opt/smart-incident-predictor/venv/bin/python src/ml/optimized_anomaly_detector.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=15
StartLimitInterval=60
StartLimitBurst=3

# Resource limits for t2.micro (lower than API service)
MemoryLimit=384M
CPUQuota=60%

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/smart-incident-predictor/logs /opt/smart-incident-predictor/data

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ml-anomaly-detector

[Install]
WantedBy=multi-user.target
EOF

# Set up log rotation for t2.micro
echo "📋 Setting up log rotation..."
cat > /etc/logrotate.d/smart-incident-predictor << 'EOF'
/opt/smart-incident-predictor/logs/*.log {
    daily
    rotate 3
    compress
    delaycompress
    missingok
    notifempty
    create 644 ec2-user ec2-user
    size 50M
    maxsize 100M
}
EOF

# Create optimized configuration
echo "⚙️ Creating optimized configuration..."
cat > /opt/smart-incident-predictor/config.yaml << 'EOF'
# Smart Incident Predictor Configuration
# Optimized for AWS t2.micro (1 vCPU, 1GB RAM)

environment: "AWS_EC2"
debug: false
log_level: "INFO"

app:
  host: "0.0.0.0"
  port: 5000
  workers: 1
  timeout: 30

ml:
  model:
    algorithm: "IsolationForest"
    contamination: 0.1
    n_estimators: 50
    max_samples: "auto"
    random_state: 42
  training:
    mode: "startup"
    min_samples: 50
    max_samples: 500
  inference:
    polling_interval: 60
    batch_size: 10
    feature_limit: 8
    sliding_window: 300
    memory_threshold_mb: 512

monitoring:
  cloudwatch:
    enabled: true
    region: "us-east-1"
    metrics_poll_interval: 60
    log_retention_days: 7
  system:
    enabled: true
    collection_interval: 120
    memory_limit_mb: 256

resources:
  max_memory_mb: 900
  max_cpu_percent: 80
  disk_space_mb: 1024
  max_processes: 50

alerting:
  enabled: true
  thresholds:
    low_risk: [0, 30]
    medium_risk: [31, 70]
    high_risk: [71, 100]
  cooldown_seconds: 300
EOF

# Set proper permissions
echo "🔐 Setting permissions..."
chown -R ec2-user:ec2-user /opt/smart-incident-predictor
chmod +x /opt/smart-incident-predictor/src/app/*.py
chmod +x /opt/smart-incident-predictor/src/ml/*.py

# Enable and start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable smart-incident-predictor
systemctl enable ml-anomaly-detector

# Start application first
echo "🌐 Starting application service..."
systemctl start smart-incident-predictor

# Wait a moment for app to start
sleep 5

# Start ML service
echo "🤖 Starting ML anomaly detector..."
systemctl start ml-anomaly-detector

# Check service status
echo "📊 Checking service status..."
systemctl status smart-incident-predictor --no-pager -l
systemctl status ml-anomaly-detector --no-pager -l

# Create health check script
echo "❤️ Creating health check script..."
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
# Health check script for Smart Incident Predictor

echo "=== Smart Incident Predictor Health Check ==="
echo "Timestamp: $(date)"
echo

# Check application service
echo "📱 Application Service:"
if systemctl is-active --quiet smart-incident-predictor; then
    echo "✅ Running"
    curl -s http://localhost:5000/health | jq '.status' 2>/dev/null || echo "⚠️ Health check failed"
else
    echo "❌ Not running"
fi

echo

# Check ML service
echo "🤖 ML Anomaly Detector:"
if systemctl is-active --quiet ml-anomaly-detector; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

echo

# Check resource usage
echo "💻 Resource Usage:"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"

echo

# Check recent logs
echo "📋 Recent Application Logs:"
journalctl -u smart-incident-predictor --no-pager -n 3 --since "5 minutes ago" | tail -3

echo
echo "📋 Recent ML Logs:"
journalctl -u ml-anomaly-detector --no-pager -n 3 --since "5 minutes ago" | tail -3

echo
echo "=== End Health Check ==="
EOF

chmod +x /usr/local/bin/health-check.sh

# Create status script
echo "📈 Creating status script..."
cat > /usr/local/bin/status-check.sh << 'EOF'
#!/bin/bash
# Quick status check for Smart Incident Predictor

echo "Smart Incident Predictor Status:"
echo "==============================="

# Application endpoint
if curl -s http://localhost:5000/health >/dev/null; then
    echo "🌐 Application: ✅ Running (http://localhost:5000)"
else
    echo "🌐 Application: ❌ Not responding"
fi

# ML service
if systemctl is-active --quiet ml-anomaly-detector; then
    echo "🤖 ML Service: ✅ Running"
else
    echo "🤖 ML Service: ❌ Not running"
fi

# Resource usage
MEMORY_USAGE=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100.0}')
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

echo "💻 Memory: ${MEMORY_USAGE}%"
echo "💻 CPU: ${CPU_USAGE}%"

# Services
echo
echo "Service Details:"
systemctl list-units --type=service --state=running | grep -E "(smart-incident-predictor|ml-anomaly-detector)"
EOF

chmod +x /usr/local/bin/status-check.sh

# Final setup
echo "🎉 Setup completed successfully!"
echo
echo "📊 Service Information:"
echo "   Application: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
echo "   Health Check: /usr/local/bin/health-check.sh"
echo "   Status Check: /usr/local/bin/status-check.sh"
echo "   Logs: journalctl -u smart-incident-predictor -f"
echo "   ML Logs: journalctl -u ml-anomaly-detector -f"
echo
echo "🔍 Management Commands:"
echo "   Restart app: sudo systemctl restart smart-incident-predictor"
echo "   Restart ML: sudo systemctl restart ml-anomaly-detector"
echo "   View status: sudo systemctl status smart-incident-predictor ml-anomaly-detector"
echo
echo "✅ Smart Incident Predictor is ready for t2.micro!"
