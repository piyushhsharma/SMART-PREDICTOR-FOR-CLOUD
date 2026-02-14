#!/usr/bin/env python3
"""
Optimized ML Anomaly Detector for AWS t2.micro
Memory-efficient, lightweight, and production-ready
"""

import logging
import time
import json
import gc
import psutil
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import config
from monitoring.cloudwatch_client import CloudWatchClient
from alerting.alert_manager import AlertManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get('log_level', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/smart-incident-predictor/logs/ml-service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    used_mb: float
    percent: float
    available_mb: float

class OptimizedAnomalyDetector:
    """Memory-efficient anomaly detection for t2.micro"""
    
    def __init__(self):
        self.ml_config = config.get_ml_config()
        self.resource_config = config.get_resource_config()
        
        # ML components
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Data management (memory optimized)
        self.training_data = []
        self.feature_buffer = []
        self.max_training_samples = self.ml_config.max_samples
        self.max_buffer_size = 100
        
        # Feature selection (optimized for t2.micro)
        self.enabled_features = config.get_enabled_features()
        self.feature_limit = min(len(self.enabled_features), self.ml_config.feature_limit)
        
        # External services
        self.cloudwatch_client = CloudWatchClient()
        self.alert_manager = AlertManager()
        
        # Performance tracking
        self.last_collection_time = time.time()
        self.prediction_count = 0
        self.memory_stats = MemoryStats(0, 0, 0)
        
        # Control flags
        self.running = False
        self.training_lock = threading.Lock()
        
        logger.info(f"Optimized anomaly detector initialized")
        logger.info(f"Features enabled: {self.enabled_features[:self.feature_limit]}")
        logger.info(f"Memory limit: {self.ml_config.memory_threshold_mb}MB")
    
    def start(self):
        """Start the anomaly detection service"""
        try:
            logger.info("Starting optimized anomaly detection service")
            self.running = True
            
            # Initial training
            if self.ml_config.training_mode == 'startup':
                self._perform_initial_training()
            
            # Start main detection loop
            self._start_detection_loop()
            
        except Exception as e:
            logger.error(f"Failed to start anomaly detector: {str(e)}")
            raise
    
    def stop(self):
        """Stop the anomaly detection service"""
        logger.info("Stopping anomaly detection service")
        self.running = False
    
    def _start_detection_loop(self):
        """Main detection loop with memory management"""
        logger.info(f"Starting detection loop with {self.ml_config.polling_interval}s interval")
        
        while self.running:
            try:
                # Check memory usage
                self._update_memory_stats()
                if self.memory_stats.used_mb > self.ml_config.memory_threshold_mb:
                    logger.warning(f"Memory usage {self.memory_stats.used_mb:.1f}MB exceeds threshold")
                    self._cleanup_memory()
                
                # Perform detection cycle
                start_time = time.time()
                self._detection_cycle()
                cycle_time = time.time() - start_time
                
                logger.debug(f"Detection cycle completed in {cycle_time:.2f}s")
                
                # Sleep for remaining time
                sleep_time = max(0, self.ml_config.polling_interval - cycle_time)
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping...")
                break
            except Exception as e:
                logger.error(f"Error in detection loop: {str(e)}")
                time.sleep(10)  # Wait before retrying
    
    def _detection_cycle(self):
        """Single detection cycle"""
        try:
            # Collect data
            features = self._collect_features()
            if not features:
                logger.debug("No features collected")
                return
            
            # Add to training data if needed
            if len(self.training_data) < self.max_training_samples:
                self._add_to_training_data(features)
            
            # Perform inference if model is trained
            if self.is_trained:
                risk_score, prediction_result = self._predict_anomaly(features)
                self._handle_prediction(risk_score, features, prediction_result)
            else:
                logger.debug("Model not trained yet, skipping prediction")
            
            # Publish health metric
            self._publish_health_metric(1)
            
        except Exception as e:
            logger.error(f"Detection cycle failed: {str(e)}")
            self._publish_health_metric(0)
    
    def _collect_features(self) -> Optional[Dict[str, Any]]:
        """Collect and optimize features"""
        try:
            # Get metrics from CloudWatch (with fallback)
            metrics = self._get_metrics_with_fallback()
            
            # Extract only enabled features (memory optimized)
            features = {}
            for feature in self.enabled_features[:self.feature_limit]:
                if feature in metrics:
                    features[feature] = metrics[feature]
                else:
                    # Use default/estimated values
                    features[feature] = self._get_default_feature_value(feature)
            
            # Add timestamp
            features['timestamp'] = datetime.utcnow().isoformat()
            
            return features
            
        except Exception as e:
            logger.error(f"Feature collection failed: {str(e)}")
            return None
    
    def _get_metrics_with_fallback(self) -> Dict[str, Any]:
        """Get metrics with CloudWatch fallback to local collection"""
        try:
            # Try CloudWatch first (if on AWS)
            if config.is_aws_ec2():
                metrics = self.cloudwatch_client.get_recent_metrics(window_minutes=2)
                if metrics:
                    return self._process_cloudwatch_metrics(metrics)
            
            # Fallback to local metrics
            return self._collect_local_metrics()
            
        except Exception as e:
            logger.debug(f"CloudWatch metrics failed, using local: {str(e)}")
            return self._collect_local_metrics()
    
    def _collect_local_metrics(self) -> Dict[str, Any]:
        """Collect metrics locally (lightweight)"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            metrics = {
                'cpu_current': cpu_percent,
                'cpu_trend': self._calculate_simple_trend([cpu_percent]),
                'memory_current': memory.percent,
                'disk_current': (disk.used / disk.total) * 100,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add estimated application metrics
            metrics.update({
                'error_rate': self._estimate_error_rate(),
                'response_time_avg': self._estimate_response_time(),
                'log_error_ratio': self._estimate_log_error_ratio(),
                'system_stress_score': self._calculate_stress_score(metrics),
                'anomaly_likelihood': 0.0  # Will be calculated
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Local metrics collection failed: {str(e)}")
            return {}
    
    def _process_cloudwatch_metrics(self, cloudwatch_metrics: Dict) -> Dict[str, Any]:
        """Process CloudWatch metrics into feature format"""
        try:
            features = {}
            
            # CPU metrics
            if 'cpu_utilization' in cloudwatch_metrics:
                cpu_data = cloudwatch_metrics['cpu_utilization']
                if cpu_data:
                    features['cpu_current'] = cpu_data[-1]
                    features['cpu_trend'] = self._calculate_simple_trend(cpu_data)
            
            # Memory metrics
            if 'memory_utilization' in cloudwatch_metrics:
                mem_data = cloudwatch_metrics['memory_utilization']
                if mem_data:
                    features['memory_current'] = mem_data[-1]
            
            # Disk metrics
            if 'disk_utilization' in cloudwatch_metrics:
                disk_data = cloudwatch_metrics['disk_utilization']
                if disk_data:
                    features['disk_current'] = disk_data[-1]
            
            # Add estimated metrics for missing data
            features.update({
                'error_rate': self._estimate_error_rate(),
                'response_time_avg': self._estimate_response_time(),
                'log_error_ratio': self._estimate_log_error_ratio(),
                'system_stress_score': self._calculate_stress_score(features),
                'anomaly_likelihood': 0.0
            })
            
            return features
            
        except Exception as e:
            logger.error(f"CloudWatch metrics processing failed: {str(e)}")
            return {}
    
    def _get_default_feature_value(self, feature: str) -> float:
        """Get default value for missing features"""
        defaults = {
            'cpu_current': 30.0,
            'cpu_trend': 0.0,
            'memory_current': 40.0,
            'error_rate': 1.0,
            'response_time_avg': 200.0,
            'log_error_ratio': 0.01,
            'system_stress_score': 0.2,
            'anomaly_likelihood': 0.0
        }
        return defaults.get(feature, 0.0)
    
    def _calculate_simple_trend(self, values: List[float]) -> float:
        """Calculate simple trend (memory efficient)"""
        if len(values) < 2:
            return 0.0
        
        # Simple difference between last two values
        return values[-1] - values[-2]
    
    def _estimate_error_rate(self) -> float:
        """Estimate error rate (simplified)"""
        # In production, this would come from actual error tracking
        return np.random.uniform(0.5, 3.0)  # Placeholder
    
    def _estimate_response_time(self) -> float:
        """Estimate response time (simplified)"""
        # In production, this would come from actual metrics
        return np.random.uniform(100, 400)  # Placeholder
    
    def _estimate_log_error_ratio(self) -> float:
        """Estimate log error ratio (simplified)"""
        # In production, this would come from log analysis
        return np.random.uniform(0.01, 0.05)  # Placeholder
    
    def _calculate_stress_score(self, metrics: Dict) -> float:
        """Calculate system stress score"""
        try:
            stress_factors = []
            
            if 'cpu_current' in metrics:
                stress_factors.append(metrics['cpu_current'] / 100)
            
            if 'memory_current' in metrics:
                stress_factors.append(metrics['memory_current'] / 100)
            
            if 'error_rate' in metrics:
                stress_factors.append(min(metrics['error_rate'] / 10, 1.0))
            
            return np.mean(stress_factors) if stress_factors else 0.0
            
        except Exception:
            return 0.0
    
    def _add_to_training_data(self, features: Dict[str, Any]):
        """Add features to training data with memory management"""
        try:
            # Create feature vector (only numeric values)
            feature_vector = []
            for feature in self.enabled_features[:self.feature_limit]:
                value = features.get(feature, 0.0)
                if isinstance(value, (int, float)):
                    feature_vector.append(value)
                else:
                    feature_vector.append(0.0)
            
            # Add to training data
            self.training_data.append(feature_vector)
            
            # Limit training data size
            if len(self.training_data) > self.max_training_samples:
                self.training_data = self.training_data[-self.max_training_samples//2:]
            
        except Exception as e:
            logger.error(f"Failed to add training data: {str(e)}")
    
    def _perform_initial_training(self):
        """Perform initial model training"""
        try:
            logger.info("Performing initial model training")
            
            # Wait for minimum samples
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while len(self.training_data) < self.ml_config.min_samples:
                if time.time() - start_time > max_wait_time:
                    logger.warning("Insufficient data for initial training")
                    return
                
                logger.info(f"Waiting for more data: {len(self.training_data)}/{self.ml_config.min_samples}")
                time.sleep(30)
                
                # Collect some data
                features = self._collect_features()
                if features:
                    self._add_to_training_data(features)
            
            # Train model
            if self._train_model():
                logger.info("Initial training completed successfully")
            else:
                logger.error("Initial training failed")
                
        except Exception as e:
            logger.error(f"Initial training failed: {str(e)}")
    
    def _train_model(self) -> bool:
        """Train the anomaly detection model"""
        try:
            with self.training_lock:
                if len(self.training_data) < self.ml_config.min_samples:
                    logger.warning(f"Insufficient data for training: {len(self.training_data)}")
                    return False
                
                logger.info(f"Training model with {len(self.training_data)} samples")
                
                # Convert to numpy array
                X = np.array(self.training_data)
                
                # Clean data (remove NaN, infinite values)
                X = np.nan_to_num(X, nan=0.0, posinf=1.0, neginf=-1.0)
                
                # Scale features
                X_scaled = self.scaler.fit_transform(X)
                
                # Create and train model (memory optimized)
                self.model = IsolationForest(
                    contamination=self.ml_config.contamination,
                    n_estimators=self.ml_config.n_estimators,
                    max_samples=self.ml_config.max_samples,
                    random_state=self.ml_config.random_state,
                    n_jobs=1  # Single thread for t2.micro
                )
                
                self.model.fit(X_scaled)
                self.is_trained = True
                
                # Cleanup training data to save memory
                self.training_data = self.training_data[-100:]  # Keep last 100 samples
                
                # Force garbage collection
                gc.collect()
                
                logger.info("Model training completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False
    
    def _predict_anomaly(self, features: Dict[str, Any]) -> tuple[float, Dict]:
        """Perform anomaly prediction"""
        try:
            # Create feature vector
            feature_vector = []
            for feature in self.enabled_features[:self.feature_limit]:
                value = features.get(feature, 0.0)
                if isinstance(value, (int, float)):
                    feature_vector.append(value)
                else:
                    feature_vector.append(0.0)
            
            # Convert to numpy and scale
            X = np.array([feature_vector])
            X = np.nan_to_num(X, nan=0.0, posinf=1.0, neginf=-1.0)
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]  # -1 for anomaly, 1 for normal
            anomaly_score = self.model.decision_function(X_scaled)[0]
            
            # Convert to risk score (0-100)
            risk_score = self._calculate_risk_score(anomaly_score, features)
            
            result = {
                'is_anomaly': prediction == -1,
                'anomaly_score': float(anomaly_score),
                'risk_score': risk_score,
                'timestamp': features.get('timestamp', datetime.utcnow().isoformat()),
                'features_used': self.enabled_features[:self.feature_limit]
            }
            
            self.prediction_count += 1
            return risk_score, result
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return 0.0, {'error': str(e)}
    
    def _calculate_risk_score(self, anomaly_score: float, features: Dict) -> float:
        """Calculate risk score from anomaly score and features"""
        try:
            # Normalize anomaly score to 0-100
            if anomaly_score < 0:
                # Anomaly detected, map to 50-100 range
                risk = min(100, 50 + abs(anomaly_score) * 50)
            else:
                # Normal, map to 0-50 range
                risk = max(0, 50 - anomaly_score * 50)
            
            # Adjust based on system stress
            stress_score = features.get('system_stress_score', 0.0)
            risk = risk * (1 + stress_score * 0.5)
            
            # Adjust based on error rate
            error_rate = features.get('error_rate', 0.0)
            if error_rate > 5:
                risk = min(100, risk * 1.2)
            
            return min(100, max(0, risk))
            
        except Exception:
            return 0.0
    
    def _handle_prediction(self, risk_score: float, features: Dict, result: Dict):
        """Handle prediction result"""
        try:
            # Log prediction
            if risk_score > 70:
                logger.warning(f"High risk detected: {risk_score:.1f}")
            elif risk_score > 40:
                logger.info(f"Medium risk detected: {risk_score:.1f}")
            else:
                logger.debug(f"Low risk: {risk_score:.1f}")
            
            # Send alert if high risk
            if risk_score > 70:
                alert_data = {
                    'risk_score': risk_score,
                    'features': features,
                    'detection_result': result,
                    'timestamp': datetime.utcnow().isoformat()
                }
                self.alert_manager.send_alert(alert_data)
            
            # Publish custom metric
            if config.is_aws_ec2():
                self.cloudwatch_client.put_custom_metric(
                    'AnomalyRiskScore', risk_score, 'None'
                )
            
        except Exception as e:
            logger.error(f"Failed to handle prediction: {str(e)}")
    
    def _publish_health_metric(self, status: int):
        """Publish health metric"""
        try:
            if config.is_aws_ec2():
                self.cloudwatch_client.put_custom_metric(
                    'MLServiceHealth', status, 'None'
                )
        except Exception as e:
            logger.debug(f"Failed to publish health metric: {str(e)}")
    
    def _update_memory_stats(self):
        """Update memory usage statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            system_memory = psutil.virtual_memory()
            
            self.memory_stats = MemoryStats(
                used_mb=memory_mb,
                percent=system_memory.percent,
                available_mb=system_memory.available / (1024 * 1024)
            )
            
        except Exception as e:
            logger.error(f"Failed to update memory stats: {str(e)}")
    
    def _cleanup_memory(self):
        """Perform memory cleanup"""
        try:
            logger.info("Performing memory cleanup")
            
            # Clear training data (keep recent samples)
            if len(self.training_data) > 50:
                self.training_data = self.training_data[-50:]
            
            # Clear feature buffer
            self.feature_buffer.clear()
            
            # Force garbage collection
            gc.collect()
            
            logger.info("Memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {str(e)}")

def main():
    """Main entry point"""
    try:
        # Create directories
        import os
        os.makedirs('/opt/smart-incident-predictor/logs', exist_ok=True)
        os.makedirs('/opt/smart-incident-predictor/data', exist_ok=True)
        
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            return 1
        
        # Create and start detector
        detector = OptimizedAnomalyDetector()
        
        try:
            detector.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            detector.stop()
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())
