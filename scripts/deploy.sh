#!/bin/bash

# Smart Incident Predictor Deployment Script
# This script handles the complete deployment process

set -e

PROJECT_NAME="smart-incident-predictor"
ENVIRONMENT=${1:-dev}

echo "🚀 Deploying Smart Incident Predictor to $ENVIRONMENT environment..."

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Step 1: Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
cd infrastructure

# Plan the deployment
echo "📋 Planning Terraform deployment..."
terraform plan -var="environment=$ENVIRONMENT" -out=tfplan

# Ask for confirmation
read -p "Do you want to apply this plan? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Applying Terraform deployment..."
    terraform apply tfplan
else
    echo "❌ Deployment cancelled"
    exit 1
fi

# Get outputs
EC2_INSTANCE_ID=$(terraform output -raw ec2_instance_id)
EC2_PUBLIC_IP=$(terraform output -raw ec2_public_ip)
SNS_TOPIC_ARN=$(terraform output -raw sns_topic_arn)

cd ..

echo "✅ Infrastructure deployed successfully!"
echo "📋 Instance Details:"
echo "   Instance ID: $EC2_INSTANCE_ID"
echo "   Public IP: $EC2_PUBLIC_IP"
echo "   SNS Topic: $SNS_TOPIC_ARN"

# Step 2: Wait for instance to be ready
echo "⏳ Waiting for EC2 instance to be ready..."
aws ec2 wait instance-running --instance-ids $EC2_INSTANCE_ID

# Step 3: Copy application files to instance
echo "📤 Copying application files to instance..."

# Create remote directory structure
ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP \
    "mkdir -p /opt/smart-incident-predictor/{src/{app,ml,monitoring,alerting},data,logs}"

# Copy source files
scp -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa -r src/ ec2-user@$EC2_PUBLIC_IP:/opt/smart-incident-predictor/

# Copy requirements
scp -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa requirements.txt ec2-user@$EC2_PUBLIC_IP:/opt/smart-incident-predictor/

# Step 4: Install dependencies and start services
echo "🔧 Installing dependencies and starting services..."

ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP << 'EOF'
cd /opt/smart-incident-predictor

# Install Python dependencies
pip3 install -r requirements.txt

# Create systemd services
sudo tee /etc/systemd/system/smart-incident-predictor.service > /dev/null << 'EOL'
[Unit]
Description=Smart Incident Predictor Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/smart-incident-predictor
ExecStart=/usr/bin/python3 src/app/sample_app.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/smart-incident-predictor/src

[Install]
WantedBy=multi-user.target
EOL

sudo tee /etc/systemd/system/ml-anomaly-detector.service > /dev/null << 'EOL'
[Unit]
Description=ML Anomaly Detection Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/smart-incident-predictor
ExecStart=/usr/bin/python3 src/ml/anomaly_detector.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/smart-incident-predictor/src

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable smart-incident-predictor
sudo systemctl enable ml-anomaly-detector
sudo systemctl start smart-incident-predictor
sudo systemctl start ml-anomaly-detector

# Check service status
sudo systemctl status smart-incident-predictor --no-pager
sudo systemctl status ml-anomaly-detector --no-pager
EOF

# Step 5: Verify deployment
echo "🔍 Verifying deployment..."

# Wait a moment for services to start
sleep 10

# Check if application is responding
if curl -s http://$EC2_PUBLIC_IP:5000/health > /dev/null; then
    echo "✅ Application is responding on port 5000"
else
    echo "⚠️ Application not responding yet, please check logs"
fi

# Step 6: Display access information
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Access Information:"
echo "   Application Health: http://$EC2_PUBLIC_IP:5000/health"
echo "   Application API: http://$EC2_PUBLIC_IP:5000/"
echo "   Metrics API: http://$EC2_PUBLIC_IP:5000/api/metrics"
echo ""
echo "🔧 Management Commands:"
echo "   SSH: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP"
echo "   View app logs: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'tail -f /opt/smart-incident-predictor/logs/application.log'"
echo "   View ML logs: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'tail -f /opt/smart-incident-predictor/logs/ml-service.log'"
echo ""
echo "📈 Next Steps:"
echo "1. Configure Grafana Cloud dashboard"
echo "2. Set up CloudWatch data source in Grafana"
echo "3. Import dashboard from grafana/dashboard.json"
echo "4. Configure alert notifications"
echo ""
echo "🔍 Monitoring:"
echo "   - Check AWS CloudWatch for metrics and logs"
echo "   - Monitor SNS topic for alerts"
echo "   - Review Grafana dashboard for system health"
