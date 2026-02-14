#!/bin/bash

# Smart Incident Predictor Deployment Script for AWS t2.micro
# Optimized for Free Tier constraints

set -e

PROJECT_NAME="smart-incident-predictor"
ENVIRONMENT=${1:-dev}
INSTANCE_TYPE="t2.micro"

echo "🚀 Deploying Smart Incident Predictor to $ENVIRONMENT environment on $INSTANCE_TYPE"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is required but not installed"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is required but not installed"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "config.yaml" ]; then
    echo "❌ Please run this script from project root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Step 1: Validate configuration
echo "✅ Validating configuration for t2.micro..."
python3 -c "
import sys
sys.path.append('src')
from config import config
if not config.validate_config():
    print('❌ Configuration validation failed for t2.micro')
    sys.exit(1)
print('✅ Configuration validated for t2.micro')
"

# Step 2: Deploy infrastructure
echo "🏗️ Deploying infrastructure for t2.micro..."
cd infrastructure

# Create terraform.tfvars file for t2.micro optimization
cat > terraform.tfvars << EOF
instance_type = "$INSTANCE_TYPE"
enable_monitoring = false
root_volume_size = 8
data_volume_size = 10
alarm_thresholds = {
  cpu_utilization_high = 75
  memory_utilization_high = 80
  disk_utilization_high = 85
}
EOF

echo "📋 Planning Terraform deployment..."
terraform plan -var-file=terraform.tfvars -var="environment=$ENVIRONMENT" -out=tfplan

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
echo "   Instance Type: $INSTANCE_TYPE"
echo "   Instance ID: $EC2_INSTANCE_ID"
echo "   Public IP: $EC2_PUBLIC_IP"
echo "   SNS Topic: $SNS_TOPIC_ARN"

# Step 3: Wait for instance to be ready
echo "⏳ Waiting for EC2 instance to be ready..."
aws ec2 wait instance-running --instance-ids $EC2_INSTANCE_ID

# Step 4: Copy application files to instance
echo "📤 Copying application files to instance..."

# Wait a bit more for instance to fully initialize
sleep 30

# Create remote directory structure
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP \
    "mkdir -p /opt/smart-incident-predictor/{src,logs,data,config}" || {
    echo "⚠️ SSH connection failed, waiting longer..."
    sleep 30
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP \
        "mkdir -p /opt/smart-incident-predictor/{src,logs,data,config}"
}

# Copy source files
echo "📁 Copying source code..."
scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i ~/.ssh/id_rsa -r src/ ec2-user@$EC2_PUBLIC_IP:/opt/smart-incident-predictor/

# Copy configuration
scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i ~/.ssh/id_rsa config.yaml ec2-user@$EC2_PUBLIC_IP:/opt/smart-incident-predictor/

# Copy requirements
scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i ~/.ssh/id_rsa requirements.txt ec2-user@$EC2_PUBLIC_IP:/opt/smart-incident-predictor/

# Step 5: Setup Python environment and dependencies
echo "🐍 Setting up Python environment on instance..."
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP << 'EOF'
cd /opt/smart-incident-predictor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (memory efficient)
pip install --no-cache-dir -r requirements.txt

echo "✅ Python environment setup completed"
EOF

# Step 6: Verify deployment
echo "🔍 Verifying deployment..."

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 60

# Check if application is responding
echo "🌐 Testing application endpoint..."
for i in {1..10}; do
    if curl -s --connect-timeout 5 http://$EC2_PUBLIC_IP:5000/health > /dev/null; then
        echo "✅ Application is responding on port 5000"
        break
    else
        echo "⏳ Waiting for application to start... (attempt $i/10)"
        sleep 10
    fi
done

# Check ML service status
echo "🤖 Checking ML service status..."
ML_STATUS=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP \
    "systemctl is-active ml-anomaly-detector 2>/dev/null || echo 'not_running'")

if [ "$ML_STATUS" = "active" ]; then
    echo "✅ ML anomaly detector is running"
else
    echo "⚠️ ML detector status: $ML_STATUS"
fi

# Step 7: Display access information
echo ""
echo "🎉 t2.micro Deployment completed successfully!"
echo ""
echo "📊 Access Information:"
echo "   Application Health: http://$EC2_PUBLIC_IP:5000/health"
echo "   Application API: http://$EC2_PUBLIC_IP:5000/"
echo "   Metrics API: http://$EC2_PUBLIC_IP:5000/api/metrics"
echo "   Status Check: http://$EC2_PUBLIC_IP:5000/api/status"
echo ""
echo "🔧 Management Commands:"
echo "   SSH: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP"
echo "   Health Check: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'health-check.sh'"
echo "   Status Check: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'status-check.sh'"
echo "   View app logs: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'journalctl -u smart-incident-predictor -f'"
echo "   View ML logs: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'journalctl -u ml-anomaly-detector -f'"
echo ""
echo "📈 t2.micro Resource Monitoring:"
echo "   Memory Usage: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'free -h'"
echo "   CPU Usage: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'top -bn1 | grep \"Cpu(s)\"'"
echo "   Disk Usage: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'df -h'"
echo ""
echo "🔍 Service Management:"
echo "   Restart app: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'sudo systemctl restart smart-incident-predictor'"
echo "   Restart ML: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'sudo systemctl restart ml-anomaly-detector'"
echo "   Service status: ssh -i ~/.ssh/id_rsa ec2-user@$EC2_PUBLIC_IP 'sudo systemctl status smart-incident-predictor ml-anomaly-detector'"
echo ""
echo "📈 Next Steps:"
echo "1. Configure Grafana Cloud dashboard"
echo "2. Set up CloudWatch data source in Grafana"
echo "3. Import dashboard from grafana/dashboard.json"
echo "4. Configure alert notifications"
echo "5. Monitor resource usage on t2.micro"
echo ""
echo "💡 t2.micro Optimization Tips:"
echo "   - Monitor memory usage (keep < 900MB)"
echo "   - Watch CPU credits (t2.micro is burstable)"
echo "   - Check log rotation (50MB limit)"
echo "   - Monitor ML service memory (384MB limit)"
echo "   - Use health checks to verify services"
echo ""
echo "🔍 Monitoring Commands:"
echo "   - Live metrics: curl -s http://$EC2_PUBLIC_IP:5000/api/metrics | jq ."
echo "   - System status: curl -s http://$EC2_PUBLIC_IP:5000/api/status | jq ."
echo "   - Configuration: curl -s http://$EC2_PUBLIC_IP:5000/api/config | jq ."
echo ""
echo "⚠️ Important Notes for t2.micro:"
echo "   - System is optimized for 1GB RAM constraint"
echo "   - ML model uses only 8 features for memory efficiency"
echo "   - Services have resource limits to prevent OOM"
echo "   - Log rotation is configured to prevent disk fill"
echo "   - Monitoring intervals are optimized for low resource usage"
echo ""
echo "🎯 Success Indicators:"
echo "   ✅ Application responds to health checks"
echo "   ✅ ML service is running and consuming memory"
echo "   ✅ Resource usage stays within t2.micro limits"
echo "   ✅ CloudWatch metrics are being collected"
echo "   ✅ Logs are being written and rotated"
