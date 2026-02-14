# t2.micro Deployment Verification Checklist

## 🚀 Pre-Deployment Verification

### Infrastructure Requirements
- [ ] AWS CLI configured with appropriate permissions
- [ ] Terraform installed and working
- [ ] SSH key pair created in AWS
- [ ] AWS Free Tier available
- [ ] Configuration file (config.yaml) reviewed

### Code Validation
- [ ] Configuration validation passes: `python3 -c "from src.config import config; config.validate_config()"`
- [ ] All Python files are syntactically correct
- [ ] Requirements file optimized for t2.micro
- [ ] Terraform files validated: `terraform validate`

---

## 🏗️ Deployment Verification

### Terraform Deployment
- [ ] `terraform plan` completes without errors
- [ ] `terraform apply` succeeds
- [ ] t2.micro instance created
- [ ] Security group configured (ports 22, 5000)
- [ ] IAM role attached correctly
- [ ] SNS topic created
- [ ] CloudWatch log groups created

### Instance Setup
- [ ] Instance is running: `aws ec2 describe-instances`
- [ ] SSH access working: `ssh -i key.pem ec2-user@IP`
- [ ] User data script executed successfully
- [ ] Python virtual environment created
- [ ] Dependencies installed without errors
- [ ] Configuration file copied correctly

---

## 🌐 Application Verification

### Service Status
```bash
# SSH into instance and run these checks
ssh -i ~/.ssh/id_rsa ec2-user@<PUBLIC_IP>
```

- [ ] Application service running: `systemctl is-active smart-incident-predictor`
- [ ] ML service running: `systemctl is-active ml-anomaly-detector`
- [ ] Services enabled on boot: `systemctl is-enabled smart-incident-predictor ml-anomaly-detector`

### Health Endpoints
- [ ] Health check responds: `curl -f http://localhost:5000/health`
- [ ] Status endpoint works: `curl http://localhost:5000/api/status`
- [ ] Metrics endpoint works: `curl http://localhost:5000/api/metrics`
- [ ] Configuration endpoint works: `curl http://localhost:5000/api/config`

### Response Validation
- [ ] Health endpoint returns status: "healthy"
- [ ] Resource monitoring shows memory < 900MB
- [ ] CPU usage < 80% on average
- [ ] Response time < 200ms
- [ ] No error responses (500, 503)

---

## 🤖 ML Service Verification

### Model Training
- [ ] Initial training completed: `journalctl -u ml-anomaly-detector | grep "training completed"`
- [ ] Model file created: `ls -la /opt/smart-incident-predictor/data/`
- [ ] Training used < 50 samples (configurable)
- [ ] Memory usage during training < 384MB

### Inference Process
- [ ] Inference running continuously: `journalctl -u ml-anomaly-detector | grep "Detection cycle"`
- [ ] Polling interval = 60 seconds (configurable)
- [ ] Risk scores being calculated
- [ ] Anomaly detection working (can be tested with stress)

### Resource Usage
```bash
# Check ML service resource usage
systemctl status ml-anomaly-detector
ps aux | grep optimized_anomaly_detector
```

- [ ] ML service memory < 384MB
- [ ] ML service CPU < 60%
- [ ] No memory leaks (stable usage over time)
- [ ] Automatic restart on failure working

---

## 📊 Monitoring Verification

### CloudWatch Integration
- [ ] Metrics being sent to CloudWatch
- [ ] Logs being sent to CloudWatch
- [ ] Custom metrics appearing: `aws cloudwatch list-metrics --namespace "Custom/ML"`
- [ ] Log groups created and receiving data

### Local Monitoring
- [ ] Application logs being written: `tail -f /opt/smart-incident-predictor/logs/application.log`
- [ ] ML service logs being written: `tail -f /opt/smart-incident-predictor/logs/ml-service.log`
- [ ] Log rotation working: `ls -la /opt/smart-incident-predictor/logs/`
- [ ] Disk usage < 85%

### Health Monitoring
- [ ] Health check script working: `/usr/local/bin/health-check.sh`
- [ ] Status check script working: `/usr/local/bin/status-check.sh`
- [ ] Resource monitoring accurate
- [ ] Service status detection working

---

## 🔒 Security Verification

### Access Control
- [ ] Non-root user for services (ec2-user)
- [ ] Proper file permissions set
- [ ] Security groups minimal (only ports 22, 5000)
- [ ] IAM roles least privilege
- [ ] No hardcoded credentials

### System Security
- [ ] Systemd service security options enabled
- [ ] Private tmp directories enabled
- [ ] File system restrictions in place
- [ ] No new privileges granted
- [ ] AppArmor/SELinux not blocking services

---

## 💰 Cost Verification

### Free Tier Usage
- [ ] EC2 t2.micro hours < 750/month
- [ ] CloudWatch logs < 5GB/month
- [ ] CloudWatch metrics < 10 custom metrics
- [ ] SNS notifications < 1M/month
- [ ] Data transfer < 15GB/month

### Cost Monitoring
- [ ] AWS Budgets set up (optional)
- [ ] Cost alerts configured (optional)
- [ ] No unexpected charges
- [ ] Resource usage within limits

---

## 🎯 Performance Verification

### Load Testing
```bash
# Generate light load
for i in {1..10}; do
    curl -s http://localhost:5000/api/metrics > /dev/null
    echo "Request $i completed"
    sleep 1
done
```

- [ ] Application handles 10 requests/minute
- [ ] Memory usage stable during load
- [ ] Response time remains < 500ms
- [ ] No service crashes during load
- [ ] ML service continues running

### Stress Testing (Optional)
```bash
# Generate CPU stress (short duration)
sudo stress --cpu 1 --timeout 30s

# Check if ML service detects anomaly
journalctl -u ml-anomaly-detector --since "2 minutes ago" | grep -i "risk"
```

- [ ] High CPU detected by ML service
- [ ] Risk score increases under stress
- [ ] Alerts generated (if configured)
- [ ] Services recover after stress ends

---

## 📈 Grafana Integration Verification

### Dashboard Setup
- [ ] Grafana Cloud account created (free tier)
- [ ] CloudWatch data source configured
- [ ] Dashboard imported successfully
- [ ] Metrics appearing in dashboard

### Data Visualization
- [ ] CPU usage graph updating
- [ ] Memory usage graph updating
- [ ] Anomaly risk score visible
- [ ] Health status indicators working
- [ ] Alert history showing

---

## 🐛 Troubleshooting Verification

### Common Issues Test
- [ ] Service restart works: `systemctl restart smart-incident-predictor`
- [ ] ML service restart works: `systemctl restart ml-anomaly-detector`
- [ ] Log rotation prevents disk fill
- [ ] Memory cleanup works under pressure
- [ ] Configuration reload works

### Debug Mode
- [ ] Debug logging can be enabled
- [ ] Verbose mode provides useful information
- [ ] Error messages are descriptive
- [ ] Stack traces captured in logs

---

## ✅ Success Criteria

### Must Have (Critical)
- [ ] **Application accessible** via HTTP on port 5000
- [ ] **Health endpoint** returns 200 OK
- [ ] **ML service** running and inferring
- [ ] **Memory usage** < 900MB total
- [ ] **Services auto-restart** on failure
- [ ] **Logs being written** and rotated
- [ ] **Cost $0/month** (Free Tier)

### Should Have (Important)
- [ ] **Resource monitoring** accurate
- [ ] **ML accuracy** > 80%
- [ ] **Response time** < 200ms
- [ ] **Uptime** > 95%
- [ ] **Grafana dashboard** functional
- [ ] **Alert system** working

### Nice to Have (Bonus)
- [ ] **Docker deployment** working
- [ ] **Load testing** passes
- [ ] **Documentation** complete
- [ ] **Monitoring scripts** helpful
- [ ] **Configuration** flexible

---

## 🎯 Final Verification

### Production Readiness
- [ ] All critical criteria met
- [ ] Documentation reviewed
- [ ] Security scan passed
- [ ] Performance acceptable
- [ ] Cost within budget
- [ ] Monitoring comprehensive

### Interview Readiness
- [ ] Demo script prepared
- [ ] Talking points rehearsed
- [ ] Troubleshooting commands known
- [ ] Architecture diagram ready
- [ ] Resume bullets updated

---

## 🚀 Deployment Confirmation

### Sign-off Checklist

- [ ] **Deployer**: _________________ Date: _______
- [ ] **Verifier**: _________________ Date: _______
- [ ] **Environment**: _________________
- [ ] **Instance ID**: _________________
- [ ] **Public IP**: _________________
- [ ] **Cost Estimate**: $0/month (Free Tier)

### Notes & Issues
________________________________________________________________
________________________________________________________________
________________________________________________________________

---

**🎉 Deployment Verified Successfully!**

The Smart Incident Predictor is now running on AWS t2.micro with optimized resource usage, demonstrating production-grade engineering under constraints.
