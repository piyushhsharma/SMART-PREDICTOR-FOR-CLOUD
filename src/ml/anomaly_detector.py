#!/usr/bin/env python3
"""
ML Anomaly Detection Service
Uses Isolation Forest to detect anomalies in system metrics and logs
"""

import logging
import time
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import pickle
import boto3
import schedule

from feature_extractor import FeatureExtractor
from risk_scorer import RiskScorer
from alert_manager import AlertManager
from cloudwatch_client import CloudWatchClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/smart-incident-predictor/logs/ml-service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Main anomaly detection service"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.risk_scorer = RiskScorer()
        self.alert_manager = AlertManager()
        self.cloudwatch_client = CloudWatchClient()
        
        # ML Model
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Configuration
        self.config = {
            'contamination': 0.1,  # Expected anomaly rate
            'window_size': 300,     # 5 minutes in seconds
            'feature_count': 15,    # Number of features
            'retrain_interval': 3600,  # Retrain every hour
            'min_samples': 100,     # Minimum samples for training
            'risk_threshold': 50    # Risk score threshold for alerts
        }
        
        # Data storage
        self.training_data = []
        self.prediction_history = []
        
        # Initialize model
        self._initialize_model()
        
        logger.info("Anomaly Detector initialized")
    
    def _initialize_model(self):
        """Initialize the Isolation Forest model"""
        try:
            self.model = IsolationForest(
                contamination=self.config['contamination'],
                random_state=42,
                n_estimators=100,
                max_samples='auto'
            )
            logger.info("Isolation Forest model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise
    
    def collect_and_process_data(self) -> Optional[Dict]:
        """Collect data from various sources and process features"""
        try:
            # Collect metrics from CloudWatch
            cloudwatch_metrics = self.cloudwatch_client.get_recent_metrics(
                window_minutes=5
            )
            
            # Collect log patterns
            log_patterns = self.cloudwatch_client.get_log_patterns(
                window_minutes=5
            )
            
            # Extract features
            features = self.feature_extractor.extract_features(
                metrics=cloudwatch_metrics,
                logs=log_patterns
            )
            
            if not features:
                logger.warning("No features extracted")
                return None
            
            # Add timestamp
            features['timestamp'] = datetime.utcnow().isoformat()
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to collect and process data: {str(e)}")
            return None
    
    def train_model(self, data: List[Dict]) -> bool:
        """Train the anomaly detection model"""
        try:
            if len(data) < self.config['min_samples']:
                logger.warning(f"Insufficient data for training: {len(data)} samples")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Remove timestamp and non-numeric columns
            feature_columns = [col for col in df.columns 
                             if col not in ['timestamp'] and df[col].dtype in ['int64', 'float64']]
            
            X = df[feature_columns].fillna(0)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled)
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            logger.info(f"Model trained successfully with {len(data)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train model: {str(e)}")
            return False
    
    def detect_anomaly(self, features: Dict) -> Tuple[bool, float, Dict]:
        """Detect anomalies in current features"""
        try:
            if not self.is_trained:
                logger.warning("Model not trained yet")
                return False, 0.0, {'status': 'model_not_trained'}
            
            # Convert to DataFrame
            df = pd.DataFrame([features])
            
            # Select numeric features
            feature_columns = [col for col in df.columns 
                             if col not in ['timestamp'] and df[col].dtype in ['int64', 'float64']]
            
            X = df[feature_columns].fillna(0)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict anomaly
            prediction = self.model.predict(X_scaled)[0]  # -1 for anomaly, 1 for normal
            anomaly_score = self.model.decision_function(X_scaled)[0]
            
            # Convert to risk score (0-100)
            risk_score = self.risk_scorer.calculate_risk_score(
                anomaly_score=anomaly_score,
                features=features
            )
            
            # Determine if anomaly
            is_anomaly = prediction == -1 or risk_score > self.config['risk_threshold']
            
            result = {
                'is_anomaly': is_anomaly,
                'risk_score': risk_score,
                'anomaly_score': float(anomaly_score),
                'prediction': int(prediction),
                'timestamp': features.get('timestamp', datetime.utcnow().isoformat()),
                'feature_contributions': self._get_feature_contributions(features)
            }
            
            return is_anomaly, risk_score, result
            
        except Exception as e:
            logger.error(f"Failed to detect anomaly: {str(e)}")
            return False, 0.0, {'error': str(e)}
    
    def _get_feature_contributions(self, features: Dict) -> Dict:
        """Get feature contributions to anomaly score"""
        try:
            contributions = {}
            
            # Simple contribution calculation based on deviation from normal
            for key, value in features.items():
                if isinstance(value, (int, float)) and key != 'timestamp':
                    # Calculate z-score contribution
                    if hasattr(self, 'feature_stats') and key in self.feature_stats:
                        mean = self.feature_stats[key]['mean']
                        std = self.feature_stats[key]['std']
                        if std > 0:
                            z_score = abs(value - mean) / std
                            contributions[key] = min(z_score * 10, 100)  # Cap at 100
                        else:
                            contributions[key] = 0
                    else:
                        contributions[key] = 0
            
            return contributions
            
        except Exception as e:
            logger.error(f"Failed to get feature contributions: {str(e)}")
            return {}
    
    def process_and_alert(self, features: Dict):
        """Process features and send alerts if anomaly detected"""
        try:
            # Detect anomaly
            is_anomaly, risk_score, result = self.detect_anomaly(features)
            
            # Store prediction history
            self.prediction_history.append(result)
            
            # Keep only last 1000 predictions
            if len(self.prediction_history) > 1000:
                self.prediction_history = self.prediction_history[-1000:]
            
            # Send alert if anomaly
            if is_anomaly:
                logger.warning(f"Anomaly detected! Risk Score: {risk_score:.2f}")
                
                # Send alert
                alert_data = {
                    'risk_score': risk_score,
                    'features': features,
                    'detection_result': result,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.alert_manager.send_alert(alert_data)
                
                # Publish custom metric to CloudWatch
                self.cloudwatch_client.put_custom_metric(
                    metric_name='AnomalyRiskScore',
                    value=risk_score,
                    unit='None'
                )
            else:
                logger.info(f"Normal operation - Risk Score: {risk_score:.2f}")
            
            # Publish health metric
            self.cloudwatch_client.put_custom_metric(
                metric_name='MLServiceHealth',
                value=1,
                unit='None'
            )
            
        except Exception as e:
            logger.error(f"Failed to process and alert: {str(e)}")
            
            # Publish health metric indicating failure
            self.cloudwatch_client.put_custom_metric(
                metric_name='MLServiceHealth',
                value=0,
                unit='None'
            )
    
    def run_continuous_detection(self):
        """Run continuous anomaly detection"""
        logger.info("Starting continuous anomaly detection")
        
        # Schedule periodic tasks
        schedule.every(1).minutes.do(self._detection_cycle)
        schedule.every(1).hours.do(self._retrain_cycle)
        
        # Initial training
        self._initial_training()
        
        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                logger.info("Stopping anomaly detection service")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(30)  # Wait before retrying
    
    def _detection_cycle(self):
        """Single detection cycle"""
        try:
            # Collect and process data
            features = self.collect_and_process_data()
            
            if features:
                # Add to training data
                self.training_data.append(features)
                
                # Process and alert
                self.process_and_alert(features)
                
                # Keep training data manageable
                if len(self.training_data) > 10000:
                    self.training_data = self.training_data[-5000:]
            
        except Exception as e:
            logger.error(f"Detection cycle failed: {str(e)}")
    
    def _retrain_cycle(self):
        """Periodic model retraining"""
        try:
            logger.info("Starting scheduled model retraining")
            
            if self.train_model(self.training_data):
                logger.info("Model retraining completed successfully")
            else:
                logger.warning("Model retraining failed")
                
        except Exception as e:
            logger.error(f"Retraining cycle failed: {str(e)}")
    
    def _initial_training(self):
        """Initial model training"""
        try:
            logger.info("Starting initial model training")
            
            # Collect initial data
            initial_data = []
            for _ in range(20):  # Collect 20 samples
                features = self.collect_and_process_data()
                if features:
                    initial_data.append(features)
                time.sleep(30)  # Wait 30 seconds between samples
            
            if initial_data:
                if self.train_model(initial_data):
                    logger.info("Initial training completed successfully")
                else:
                    logger.warning("Initial training failed, will retry later")
            else:
                logger.warning("No initial data collected")
                
        except Exception as e:
            logger.error(f"Initial training failed: {str(e)}")
    
    def _save_model(self):
        """Save the trained model"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'config': self.config,
                'feature_stats': getattr(self, 'feature_stats', {})
            }
            
            with open('/opt/smart-incident-predictor/data/anomaly_model.pkl', 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info("Model saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
    
    def _load_model(self):
        """Load a saved model"""
        try:
            with open('/opt/smart-incident-predictor/data/anomaly_model.pkl', 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.config = model_data.get('config', self.config)
            self.feature_stats = model_data.get('feature_stats', {})
            self.is_trained = True
            
            logger.info("Model loaded successfully")
            return True
            
        except FileNotFoundError:
            logger.info("No saved model found")
            return False
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False

def main():
    """Main entry point"""
    try:
        # Create data directory
        import os
        os.makedirs('/opt/smart-incident-predictor/data', exist_ok=True)
        
        # Initialize detector
        detector = AnomalyDetector()
        
        # Try to load existing model
        if not detector._load_model():
            logger.info("No existing model found, will train with new data")
        
        # Start continuous detection
        detector.run_continuous_detection()
        
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        raise

if __name__ == '__main__':
    main()
