#!/usr/bin/env python3
"""
Risk Scorer for Anomaly Detection
Calculates incident risk scores based on anomaly detection results
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class RiskScorer:
    """Calculates risk scores for detected anomalies"""
    
    def __init__(self):
        # Risk scoring configuration
        self.risk_config = {
            'weights': {
                'anomaly_score': 0.4,      # ML model anomaly score
                'system_stress': 0.25,     # System stress indicators
                'error_rate': 0.2,         # Error rate impact
                'performance': 0.15        # Performance degradation
            },
            'thresholds': {
                'low_risk': (0, 30),
                'medium_risk': (31, 70),
                'high_risk': (71, 100)
            },
            'severity_multipliers': {
                'critical_system': 1.5,
                'customer_facing': 1.3,
                'internal_service': 1.0,
                'background_task': 0.7
            }
        }
        
        # Historical context
        self.prediction_history = []
        self.baseline_metrics = {}
        
        logger.info("Risk Scorer initialized")
    
    def calculate_risk_score(self, anomaly_score: float, features: Dict) -> float:
        """Calculate comprehensive risk score"""
        try:
            # Normalize anomaly score (-1 to 1) to (0 to 100)
            normalized_anomaly_score = self._normalize_anomaly_score(anomaly_score)
            
            # Calculate component scores
            system_stress_score = self._calculate_system_stress_score(features)
            error_rate_score = self._calculate_error_rate_score(features)
            performance_score = self._calculate_performance_score(features)
            
            # Calculate weighted risk score
            risk_score = (
                normalized_anomaly_score * self.risk_config['weights']['anomaly_score'] +
                system_stress_score * self.risk_config['weights']['system_stress'] +
                error_rate_score * self.risk_config['weights']['error_rate'] +
                performance_score * self.risk_config['weights']['performance']
            )
            
            # Apply severity multipliers
            risk_score = self._apply_severity_multipliers(risk_score, features)
            
            # Apply temporal context
            risk_score = self._apply_temporal_context(risk_score)
            
            # Ensure score is within bounds
            risk_score = max(0, min(100, risk_score))
            
            # Store for historical context
            self._store_prediction(risk_score, features)
            
            return round(risk_score, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate risk score: {str(e)}")
            return 0.0
    
    def _normalize_anomaly_score(self, anomaly_score: float) -> float:
        """Normalize ML anomaly score to 0-100 scale"""
        # Isolation Forest returns: negative for anomalies, positive for normal
        # Convert to 0-100 where higher is more anomalous
        if anomaly_score < 0:
            # Anomaly detected, map to 50-100 range
            return min(100, 50 + abs(anomaly_score) * 50)
        else:
            # Normal, map to 0-50 range
            return max(0, 50 - anomaly_score * 50)
    
    def _calculate_system_stress_score(self, features: Dict) -> float:
        """Calculate system stress component score"""
        try:
            stress_indicators = []
            
            # CPU stress
            cpu_current = features.get('cpu_current', 0)
            if cpu_current > 90:
                stress_indicators.append(100)
            elif cpu_current > 80:
                stress_indicators.append(75)
            elif cpu_current > 70:
                stress_indicators.append(50)
            elif cpu_current > 50:
                stress_indicators.append(25)
            else:
                stress_indicators.append(0)
            
            # Memory stress
            memory_current = features.get('memory_current', 0)
            if memory_current > 95:
                stress_indicators.append(100)
            elif memory_current > 85:
                stress_indicators.append(75)
            elif memory_current > 75:
                stress_indicators.append(50)
            elif memory_current > 60:
                stress_indicators.append(25)
            else:
                stress_indicators.append(0)
            
            # Disk stress
            disk_current = features.get('disk_current', 0)
            if disk_current > 95:
                stress_indicators.append(100)
            elif disk_current > 85:
                stress_indicators.append(75)
            elif disk_current > 75:
                stress_indicators.append(50)
            else:
                stress_indicators.append(0)
            
            # System stress score (if available)
            system_stress = features.get('system_stress_score', 0)
            stress_indicators.append(system_stress * 100)
            
            return np.mean(stress_indicators)
            
        except Exception as e:
            logger.error(f"Failed to calculate system stress score: {str(e)}")
            return 0.0
    
    def _calculate_error_rate_score(self, float) -> float:
        """Calculate error rate component score"""
        try:
            # Log error ratio
            log_error_ratio = features.get('log_error_ratio', 0)
            
            # Error spike detection
            error_spike = features.get('recent_error_spike', 1)
            
            # Error types diversity
            error_types = features.get('error_types_count', 0)
            
            # Calculate error score
            error_score = 0
            
            # Base error rate score
            if log_error_ratio > 0.2:  # >20% errors
                error_score += 80
            elif log_error_ratio > 0.1:  # >10% errors
                error_score += 60
            elif log_error_ratio > 0.05:  # >5% errors
                error_score += 40
            elif log_error_ratio > 0.01:  # >1% errors
                error_score += 20
            
            # Error spike penalty
            if error_spike > 5:  # 5x increase
                error_score += 40
            elif error_spike > 3:  # 3x increase
                error_score += 25
            elif error_spike > 2:  # 2x increase
                error_score += 15
            
            # Error diversity penalty
            if error_types > 5:
                error_score += 20
            elif error_types > 3:
                error_score += 10
            elif error_types > 1:
                error_score += 5
            
            return min(100, error_score)
            
        except Exception as e:
            logger.error(f"Failed to calculate error rate score: {str(e)}")
            return 0.0
    
    def _calculate_performance_score(self, features: Dict) -> float:
        """Calculate performance degradation score"""
        try:
            performance_score = 0
            
            # Response time metrics
            response_time_current = features.get('response_time_current', 0)
            response_time_p95 = features.get('response_time_p95', 0)
            log_response_time_p95 = features.get('log_response_time_p95', 0)
            
            # Current response time
            if response_time_current > 5000:  # >5 seconds
                performance_score += 80
            elif response_time_current > 2000:  # >2 seconds
                performance_score += 60
            elif response_time_current > 1000:  # >1 second
                performance_score += 40
            elif response_time_current > 500:  # >500ms
                performance_score += 20
            
            # P95 response time
            if response_time_p95 > 3000:
                performance_score += 60
            elif response_time_p95 > 1500:
                performance_score += 40
            elif response_time_p95 > 800:
                performance_score += 20
            
            # Log-based response time
            if log_response_time_p95 > 2000:
                performance_score += 40
            elif log_response_time_p95 > 1000:
                performance_score += 25
            elif log_response_time_p95 > 500:
                performance_score += 10
            
            # Slow requests ratio
            slow_requests_ratio = features.get('slow_requests_ratio', 0)
            if slow_requests_ratio > 0.2:  # >20% slow requests
                performance_score += 50
            elif slow_requests_ratio > 0.1:  # >10% slow requests
                performance_score += 30
            elif slow_requests_ratio > 0.05:  # >5% slow requests
                performance_score += 15
            
            return min(100, performance_score)
            
        except Exception as e:
            logger.error(f"Failed to calculate performance score: {str(e)}")
            return 0.0
    
    def _apply_severity_multipliers(self, risk_score: float, features: Dict) -> float:
        """Apply severity multipliers based on affected components"""
        try:
            multiplier = 1.0
            
            # Check for critical system indicators
            if features.get('cpu_current', 0) > 95 or features.get('memory_current', 0) > 98:
                multiplier *= self.risk_config['severity_multipliers']['critical_system']
            
            # Check for customer-facing impact
            error_patterns = features.get('log_pattern_connection_ratio', 0)
            if error_patterns > 0.1:  # High connection errors
                multiplier *= self.risk_config['severity_multipliers']['customer_facing']
            
            # Check for database issues
            db_patterns = features.get('log_pattern_database_ratio', 0)
            if db_patterns > 0.05:  # Database errors
                multiplier *= self.risk_config['severity_multipliers']['customer_facing']
            
            return risk_score * multiplier
            
        except Exception as e:
            logger.error(f"Failed to apply severity multipliers: {str(e)}")
            return risk_score
    
    def _apply_temporal_context(self, risk_score: float) -> float:
        """Apply temporal context to risk score"""
        try:
            # Check if this is part of a pattern
            recent_predictions = self.prediction_history[-10:]  # Last 10 predictions
            
            if len(recent_predictions) >= 3:
                recent_scores = [p['risk_score'] for p in recent_predictions]
                
                # Increasing trend
                if len(recent_scores) >= 3:
                    trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
                    if trend > 5:  # Increasing trend
                        risk_score *= 1.2
                    elif trend < -5:  # Decreasing trend
                        risk_score *= 0.9
                
                # Sustained high risk
                if np.mean(recent_scores[-3:]) > 60:
                    risk_score *= 1.1
            
            # Time of day considerations
            current_hour = datetime.now().hour
            if 2 <= current_hour <= 5:  # Off-peak hours
                risk_score *= 1.1  # Issues during off-peak are more concerning
            elif 9 <= current_hour <= 17:  # Business hours
                risk_score *= 1.05  # Slightly higher impact during business hours
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Failed to apply temporal context: {str(e)}")
            return risk_score
    
    def _store_prediction(self, risk_score: float, features: Dict):
        """Store prediction for historical context"""
        try:
            prediction = {
                'timestamp': datetime.utcnow().isoformat(),
                'risk_score': risk_score,
                'features': features
            }
            
            self.prediction_history.append(prediction)
            
            # Keep only last 1000 predictions
            if len(self.prediction_history) > 1000:
                self.prediction_history = self.prediction_history[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to store prediction: {str(e)}")
    
    def get_risk_level(self, risk_score: float) -> str:
        """Get risk level classification"""
        if risk_score >= self.risk_config['thresholds']['high_risk'][0]:
            return 'HIGH'
        elif risk_score >= self.risk_config['thresholds']['medium_risk'][0]:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_risk_description(self, risk_score: float, features: Dict) -> str:
        """Get human-readable risk description"""
        try:
            risk_level = self.get_risk_level(risk_score)
            
            if risk_level == 'HIGH':
                return self._get_high_risk_description(features)
            elif risk_level == 'MEDIUM':
                return self._get_medium_risk_description(features)
            else:
                return self._get_low_risk_description(features)
                
        except Exception as e:
            logger.error(f"Failed to generate risk description: {str(e)}")
            return f"Risk score: {risk_score:.2f}"
    
    def _get_high_risk_description(self, features: Dict) -> str:
        """Generate high risk description"""
        issues = []
        
        if features.get('cpu_current', 0) > 90:
            issues.append("critical CPU usage")
        if features.get('memory_current', 0) > 95:
            issues.append("critical memory usage")
        if features.get('log_error_ratio', 0) > 0.1:
            issues.append("high error rate")
        if features.get('response_time_current', 0) > 2000:
            issues.append("severe performance degradation")
        
        if issues:
            return f"CRITICAL: {', '.join(issues)}. Immediate action required."
        else:
            return "CRITICAL: Multiple system anomalies detected. Immediate investigation required."
    
    def _get_medium_risk_description(self, features: Dict) -> str:
        """Generate medium risk description"""
        issues = []
        
        if features.get('cpu_current', 0) > 70:
            issues.append("elevated CPU usage")
        if features.get('memory_current', 0) > 75:
            issues.append("elevated memory usage")
        if features.get('log_error_ratio', 0) > 0.05:
            issues.append("increased error rate")
        if features.get('response_time_current', 0) > 1000:
            issues.append("performance degradation")
        
        if issues:
            return f"WARNING: {', '.join(issues)}. Monitor closely."
        else:
            return "WARNING: System anomalies detected. Monitor closely."
    
    def _get_low_risk_description(self, features: Dict) -> str:
        """Generate low risk description"""
        return "INFO: Minor anomalies detected. Normal operation expected."
