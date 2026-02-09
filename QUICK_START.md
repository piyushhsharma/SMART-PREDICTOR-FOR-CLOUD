# Quick Start Guide

## 🚀 5-Minute Deployment

### Prerequisites
- AWS CLI configured with free tier access
- Terraform installed
- Python 3.8+
- Git

### Step 1: Clone and Setup
```bash
git clone <repository-url>
cd smart-incident-predictor
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Step 2: Deploy Infrastructure
```bash
cd infrastructure
terraform plan
terraform apply
```

### Step 3: Access the Application
```bash
# Get the public IP from Terraform output
terraform output ec2_public_ip

# Test the application
curl http://<PUBLIC_IP>:5000/health
```

### Step 4: View Dashboard
1. Sign up for Grafana Cloud (free tier)
2. Import `grafana/dashboard.json`
3. Configure CloudWatch data source
4. View live metrics at your Grafana URL

## 🔍 What You'll See

### Application Endpoints
- **Health Check**: `http://<IP>:5000/health`
- **Main App**: `http://<IP>:5000/`
- **Metrics API**: `http://<IP>:5000/api/metrics`

### Monitoring Dashboard
- Real-time CPU, Memory, Disk usage
- ML anomaly risk scores (0-100)
- Alert history and predictions
- System health indicators

### Alert Examples
```
🚨 HIGH RISK INCIDENT PREDICTED
Risk Score: 85/100
Responsible Metric: CPU Usage (95%)
Prediction: System overload expected in 8 minutes
```

## 📊 Key Metrics to Watch

1. **Anomaly Risk Score** - 0-100 scale
   - 0-30: Normal operation
   - 31-70: Monitor closely
   - 71-100: Immediate action required

2. **System Health Indicators**
   - CPU Usage < 80%
   - Memory Usage < 85%
   - Error Rate < 5%

3. **ML Service Status**
   - Should show "UP" in dashboard
   - Check logs if service is down

## 🛠️ Troubleshooting

### Common Issues

**ML Service Not Starting**
```bash
ssh -i ~/.ssh/id_rsa ec2-user@<IP>
sudo systemctl status ml-anomaly-detector
sudo journalctl -u ml-anomaly-detector -f
```

**No Metrics in CloudWatch**
```bash
# Check CloudWatch agent status
sudo systemctl status amazon-cloudwatch-agent
# Restart if needed
sudo systemctl restart amazon-cloudwatch-agent
```

**Application Not Responding**
```bash
# Check application logs
tail -f /opt/smart-incident-predictor/logs/application.log
# Restart service
sudo systemctl restart smart-incident-predictor
```

### Generate Test Anomalies

```bash
# SSH into instance
ssh -i ~/.ssh/id_rsa ec2-user@<IP>

# Generate CPU stress
sudo stress --cpu 4 --timeout 60s

# Generate memory stress
sudo stress --vm 2 --vm-bytes 512M --timeout 60s

# Watch ML service detect anomalies
tail -f /opt/smart-incident-predictor/logs/ml-service.log
```

## 📈 Expected Results

Within 10 minutes of deployment, you should see:

1. **Live Metrics**: CPU, Memory, Disk graphs updating
2. **ML Predictions**: Risk scores being calculated
3. **Sample Logs**: Application generating realistic log patterns
4. **Alert System**: Ready to send notifications

## 🎯 Success Indicators

✅ Infrastructure deployed without errors  
✅ Application health check returns 200  
✅ ML service is running and healthy  
✅ Grafana dashboard shows live data  
✅ Risk scores are being calculated  
✅ Sample alerts can be generated  

## 📞 Support

### Log Locations
- Application: `/opt/smart-incident-predictor/logs/application.log`
- ML Service: `/opt/smart-incident-predictor/logs/ml-service.log`
- System: `journalctl -u amazon-cloudwatch-agent`

### Useful Commands
```bash
# Check all services
sudo systemctl status smart-incident-predictor ml-anomaly-detector amazon-cloudwatch-agent

# View recent logs
tail -f /opt/smart-incident-predictor/logs/*.log

# Test API endpoints
curl http://localhost:5000/api/metrics
curl http://localhost:5000/health

# Check CloudWatch metrics
aws cloudwatch list-metrics --namespace "Custom/ML"
```

## 🔄 Cleanup

To remove all resources and avoid charges:
```bash
cd infrastructure
terraform destroy
```

---

**🎉 Congratulations!** You now have a production-grade ML-powered incident prediction system running in the cloud!
