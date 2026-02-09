#!/bin/bash

# Smart Incident Predictor Setup Script
# This script sets up the environment and dependencies

set -e

echo "🚀 Setting up Smart Incident Predictor..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📦 Found Python version: $PYTHON_VERSION"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is required but not installed. Please install AWS CLI"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is required but not installed. Please install Terraform"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Set up AWS credentials check
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️ AWS credentials not configured. Please run 'aws configure'"
    echo "   Make sure you have appropriate permissions for:"
    echo "   - EC2 instances"
    echo "   - CloudWatch logs and metrics"
    echo "   - SNS topics"
    echo "   - IAM roles"
fi

# Initialize Terraform
echo "🏗️ Initializing Terraform..."
cd infrastructure
terraform init
cd ..

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Configure AWS credentials: aws configure"
echo "2. Review and customize infrastructure variables in infrastructure/variables.tf"
echo "3. Deploy infrastructure: cd infrastructure && terraform plan && terraform apply"
echo "4. Start the application: python src/app/sample_app.py"
echo "5. Start ML service: python src/ml/anomaly_detector.py"
echo ""
echo "📊 For Grafana dashboard:"
echo "1. Sign up for Grafana Cloud free tier"
echo "2. Import dashboard from grafana/dashboard.json"
echo "3. Configure CloudWatch data source"
echo ""
echo "🔍 Monitor logs in:"
echo "- Application logs: tail -f logs/application.log"
echo "- ML service logs: tail -f logs/ml-service.log"
