#!/usr/bin/env python3
"""
Alert Manager for Anomaly Detection
Handles alert generation and notification delivery
"""

import logging
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """Alert data structure"""
    timestamp: str
    risk_score: float
    risk_level: str
    description: str
    responsible_metrics: List[str]
    recommendations: List[str]
    incident_id: str

class AlertManager:
    """Manages alert generation and delivery"""
    
    def __init__(self):
        self.sns_client = boto3.client('sns')
        self.cloudwatch_client = boto3.client('cloudwatch')
        
        # Alert configuration
        self.alert_config = {
            'sns_topic_arn': self._get_sns_topic_arn(),
            'min_alert_interval': 300,  # 5 minutes between same type alerts
            'alert_cooldown': {},  # Track alert cooldowns
            'incident_counter': 0
        }
        
        # Alert templates
        self.alert_templates = {
            'HIGH': {
                'emoji': '🚨',
                'subject': 'CRITICAL: High Risk Incident Predicted',
                'priority': 'CRITICAL'
            },
            'MEDIUM': {
                'emoji': '⚠️',
                'subject': 'WARNING: Medium Risk Anomaly Detected',
                'priority': 'HIGH'
            },
            'LOW': {
                'emoji': 'ℹ️',
                'subject': 'INFO: Low Risk Anomaly Detected',
                'priority': 'MEDIUM'
            }
        }
        
        logger.info("Alert Manager initialized")
    
    def send_alert(self, alert_data: Dict):
        """Send alert based on anomaly detection results"""
        try:
            risk_score = alert_data.get('risk_score', 0)
            features = alert_data.get('features', {})
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Check cooldown
            if self._is_in_cooldown(risk_level):
                logger.info(f"Alert for {risk_level} risk is in cooldown period")
                return
            
            # Create alert
            alert = self._create_alert(risk_score, risk_level, features)
            
            # Send notifications
            self._send_console_alert(alert)
            self._send_sns_alert(alert)
            self._send_cloudwatch_metric(alert)
            
            # Update cooldown
            self._update_cooldown(risk_level)
            
            logger.info(f"Alert sent: {alert.incident_id} - {risk_level} risk ({risk_score:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= 71:
            return 'HIGH'
        elif risk_score >= 31:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _create_alert(self, risk_score: float, risk_level: str, features: Dict) -> Alert:
        """Create alert object"""
        # Generate incident ID
        self.alert_config['incident_counter'] += 1
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{self.alert_config['incident_counter']:04d}"
        
        # Identify responsible metrics
        responsible_metrics = self._identify_responsible_metrics(features, risk_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(features, risk_level)
        
        # Generate description
        description = self._generate_alert_description(risk_score, risk_level, features)
        
        return Alert(
            timestamp=datetime.utcnow().isoformat(),
            risk_score=risk_score,
            risk_level=risk_level,
            description=description,
            responsible_metrics=responsible_metrics,
            recommendations=recommendations,
            incident_id=incident_id
        )
    
    def _identify_responsible_metrics(self, features: Dict, risk_score: float) -> List[str]:
        """Identify metrics most responsible for the alert"""
        responsible = []
        
        # CPU issues
        cpu_current = features.get('cpu_current', 0)
        if cpu_current > 80:
            responsible.append(f"CPU Usage ({cpu_current:.1f}%)")
        
        # Memory issues
        memory_current = features.get('memory_current', 0)
        if memory_current > 80:
            responsible.append(f"Memory Usage ({memory_current:.1f}%)")
        
        # Error rate
        error_ratio = features.get('log_error_ratio', 0)
        if error_ratio > 0.05:
            responsible.append(f"Error Rate ({error_ratio*100:.1f}%)")
        
        # Response time
        response_time = features.get('response_time_current', 0)
        if response_time > 1000:
            responsible.append(f"Response Time ({response_time:.0f}ms)")
        
        # System stress
        stress_score = features.get('system_stress_score', 0)
        if stress_score > 0.7:
            responsible.append(f"System Stress ({stress_score*100:.1f}%)")
        
        # If no specific issues, use general anomaly
        if not responsible:
            responsible.append("ML Anomaly Detection")
        
        return responsible
    
    def _generate_recommendations(self, features: Dict, risk_level: str) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # CPU recommendations
        cpu_current = features.get('cpu_current', 0)
        if cpu_current > 90:
            recommendations.append("Scale up CPU resources immediately")
            recommendations.append("Check for CPU-intensive processes")
        elif cpu_current > 70:
            recommendations.append("Monitor CPU usage closely")
            recommendations.append("Consider scaling up if trend continues")
        
        # Memory recommendations
        memory_current = features.get('memory_current', 0)
        if memory_current > 90:
            recommendations.append("Scale up memory resources immediately")
            recommendations.append("Check for memory leaks")
        elif memory_current > 75:
            recommendations.append("Monitor memory usage trends")
        
        # Error rate recommendations
        error_ratio = features.get('log_error_ratio', 0)
        if error_ratio > 0.1:
            recommendations.append("Investigate recent deployments")
            recommendations.append("Check database connectivity")
        elif error_ratio > 0.05:
            recommendations.append("Review recent error logs")
        
        # Performance recommendations
        response_time = features.get('response_time_current', 0)
        if response_time > 2000:
            recommendations.append("Investigate performance bottlenecks")
            recommendations.append("Check external service dependencies")
        elif response_time > 1000:
            recommendations.append("Monitor application performance")
        
        # Risk level specific recommendations
        if risk_level == 'HIGH':
            recommendations.insert(0, "IMMEDIATE ACTION REQUIRED")
            recommendations.append("Consider incident response procedures")
        elif risk_level == 'MEDIUM':
            recommendations.append("Prepare for potential escalation")
            recommendations.append("Notify on-call engineer")
        
        # If no specific recommendations
        if not recommendations:
            recommendations.append("Continue monitoring system metrics")
            recommendations.append("Review anomaly detection patterns")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _generate_alert_description(self, risk_score: float, risk_level: str, features: Dict) -> str:
        """Generate alert description"""
        template = self.alert_templates.get(risk_level, {})
        emoji = template.get('emoji', '🔍')
        
        # Base description
        description = f"{emoji} {risk_level} RISK INCIDENT PREDICTED\n"
        description += f"Risk Score: {risk_score:.1f}/100\n"
        description += f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        # Add key metrics
        description += "KEY METRICS:\n"
        
        cpu_current = features.get('cpu_current', 0)
        if cpu_current > 0:
            description += f"• CPU Usage: {cpu_current:.1f}%\n"
        
        memory_current = features.get('memory_current', 0)
        if memory_current > 0:
            description += f"• Memory Usage: {memory_current:.1f}%\n"
        
        error_ratio = features.get('log_error_ratio', 0)
        if error_ratio > 0:
            description += f"• Error Rate: {error_ratio*100:.2f}%\n"
        
        response_time = features.get('response_time_current', 0)
        if response_time > 0:
            description += f"• Response Time: {response_time:.0f}ms\n"
        
        # Add prediction
        description += f"\nPREDICTION: "
        if risk_level == 'HIGH':
            description += "System failure expected within 5-10 minutes"
        elif risk_level == 'MEDIUM':
            description += "Performance degradation likely within 15-30 minutes"
        else:
            description += "Minor issues may affect user experience"
        
        return description
    
    def _send_console_alert(self, alert: Alert):
        """Send alert to console/logs"""
        try:
            # Format console message
            console_message = f"""
{'='*60}
🚨 SMART INCIDENT PREDICTOR ALERT 🚨
{'='*60}
Incident ID: {alert.incident_id}
Risk Level: {alert.risk_level}
Risk Score: {alert.risk_score:.2f}/100
Timestamp: {alert.timestamp}

DESCRIPTION:
{alert.description}

RESPONSIBLE METRICS:
{chr(10).join(f"• {metric}" for metric in alert.responsible_metrics)}

RECOMMENDATIONS:
{chr(10).join(f"• {rec}" for rec in alert.recommendations)}

{'='*60}
"""
            
            logger.warning(console_message)
            
        except Exception as e:
            logger.error(f"Failed to send console alert: {str(e)}")
    
    def _send_sns_alert(self, alert: Alert):
        """Send alert via SNS"""
        try:
            if not self.alert_config['sns_topic_arn']:
                logger.warning("SNS topic ARN not configured")
                return
            
            # Prepare SNS message
            template = self.alert_templates.get(alert.risk_level, {})
            
            message = {
                'incident_id': alert.incident_id,
                'risk_level': alert.risk_level,
                'risk_score': alert.risk_score,
                'timestamp': alert.timestamp,
                'description': alert.description,
                'responsible_metrics': alert.responsible_metrics,
                'recommendations': alert.recommendations,
                'priority': template.get('priority', 'MEDIUM')
            }
            
            # Send to SNS
            response = self.sns_client.publish(
                TopicArn=self.alert_config['sns_topic_arn'],
                Subject=template.get('subject', f'Alert: {alert.risk_level} Risk'),
                Message=json.dumps(message, indent=2),
                MessageStructure='string'
            )
            
            logger.info(f"SNS alert sent: {response.get('MessageId')}")
            
        except Exception as e:
            logger.error(f"Failed to send SNS alert: {str(e)}")
    
    def _send_cloudwatch_metric(self, alert: Alert):
        """Send alert metric to CloudWatch"""
        try:
            # Put custom metric
            self.cloudwatch_client.put_metric_data(
                Namespace='Custom/ML',
                MetricData=[
                    {
                        'MetricName': 'AlertRiskScore',
                        'Value': alert.risk_score,
                        'Unit': 'None',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {
                                'Name': 'RiskLevel',
                                'Value': alert.risk_level
                            },
                            {
                                'Name': 'IncidentID',
                                'Value': alert.incident_id
                            }
                        ]
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to send CloudWatch metric: {str(e)}")
    
    def _is_in_cooldown(self, risk_level: str) -> bool:
        """Check if alert type is in cooldown"""
        try:
            last_alert_time = self.alert_config['alert_cooldown'].get(risk_level)
            if not last_alert_time:
                return False
            
            cooldown_period = self.alert_config['min_alert_interval']
            current_time = datetime.utcnow()
            
            return (current_time - last_alert_time).total_seconds() < cooldown_period
            
        except Exception:
            return False
    
    def _update_cooldown(self, risk_level: str):
        """Update cooldown for alert type"""
        try:
            self.alert_config['alert_cooldown'][risk_level] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to update cooldown: {str(e)}")
    
    def _get_sns_topic_arn(self) -> Optional[str]:
        """Get SNS topic ARN from environment or configuration"""
        try:
            # In production, this would come from environment variables or config
            # For demo, we'll try to find it from AWS
            sns = boto3.client('sns')
            topics = sns.list_topics()
            
            for topic in topics.get('Topics', []):
                topic_arn = topic['TopicArn']
                if 'smart-incident-predictor-alerts' in topic_arn:
                    return topic_arn
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get SNS topic ARN: {str(e)}")
            return None
    
    def get_alert_statistics(self, hours: int = 24) -> Dict:
        """Get alert statistics for the last N hours"""
        try:
            # This would typically query a database or logs
            # For demo, return mock statistics
            return {
                'total_alerts': 0,
                'high_risk_alerts': 0,
                'medium_risk_alerts': 0,
                'low_risk_alerts': 0,
                'average_risk_score': 0,
                'peak_risk_score': 0,
                'time_period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {str(e)}")
            return {}
