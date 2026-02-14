#!/usr/bin/env python3
"""
Configuration Management for Smart Incident Predictor
Optimized for AWS t2.micro constraints
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """Application configuration"""
    host: str = "0.0.0.0"
    port: int = 5000
    workers: int = 1
    timeout: int = 30
    debug: bool = False
    log_level: str = "INFO"

@dataclass
class MLConfig:
    """ML service configuration"""
    algorithm: str = "IsolationForest"
    contamination: float = 0.1
    n_estimators: int = 50
    max_samples: str = "auto"
    random_state: int = 42
    polling_interval: int = 60
    batch_size: int = 10
    feature_limit: int = 8
    sliding_window: int = 300
    memory_threshold_mb: int = 512
    training_mode: str = "startup"
    min_samples: int = 50
    max_samples: int = 500

@dataclass
class ResourceConfig:
    """Resource limits configuration"""
    max_memory_mb: int = 900
    max_cpu_percent: int = 80
    disk_space_mb: int = 1024
    max_processes: int = 50

class ConfigManager:
    """Configuration manager with environment-specific loading"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
        self.environment = self._get_environment()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return self._get_default_config()
    
    def _get_environment(self) -> str:
        """Get current environment"""
        env = os.getenv('ENVIRONMENT', '').upper()
        if not env:
            # Auto-detect environment
            if os.path.exists('/sys/hypervisor/uuid'):
                env = 'AWS_EC2'
            else:
                env = 'LOCAL'
        
        logger.info(f"Environment detected: {env}")
        return env
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'environment': 'LOCAL',
            'debug': True,
            'log_level': 'INFO',
            'app': {
                'host': '0.0.0.0',
                'port': 5000,
                'workers': 1,
                'timeout': 30
            },
            'ml': {
                'model': {
                    'algorithm': 'IsolationForest',
                    'contamination': 0.1,
                    'n_estimators': 50,
                    'max_samples': 'auto',
                    'random_state': 42
                },
                'training': {
                    'mode': 'startup',
                    'min_samples': 50,
                    'max_samples': 500
                },
                'inference': {
                    'polling_interval': 60,
                    'batch_size': 10,
                    'feature_limit': 8,
                    'sliding_window': 300,
                    'memory_threshold_mb': 512
                }
            },
            'resources': {
                'max_memory_mb': 900,
                'max_cpu_percent': 80,
                'disk_space_mb': 1024
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            # Override with environment variables
            env_key = key.upper().replace('.', '_')
            env_value = os.getenv(env_key)
            if env_value is not None:
                return self._convert_env_value(env_value)
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get config key {key}: {str(e)}")
            return default
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable to appropriate type"""
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get_app_config(self) -> AppConfig:
        """Get application configuration"""
        return AppConfig(
            host=self.get('app.host', '0.0.0.0'),
            port=self.get('app.port', 5000),
            workers=self.get('app.workers', 1),
            timeout=self.get('app.timeout', 30),
            debug=self.get('debug', False),
            log_level=self.get('log_level', 'INFO')
        )
    
    def get_ml_config(self) -> MLConfig:
        """Get ML configuration"""
        return MLConfig(
            algorithm=self.get('ml.model.algorithm', 'IsolationForest'),
            contamination=self.get('ml.model.contamination', 0.1),
            n_estimators=self.get('ml.model.n_estimators', 50),
            max_samples=self.get('ml.model.max_samples', 'auto'),
            random_state=self.get('ml.model.random_state', 42),
            polling_interval=self.get('ml.inference.polling_interval', 60),
            batch_size=self.get('ml.inference.batch_size', 10),
            feature_limit=self.get('ml.inference.feature_limit', 8),
            sliding_window=self.get('ml.inference.sliding_window', 300),
            memory_threshold_mb=self.get('ml.inference.memory_threshold_mb', 512),
            training_mode=self.get('ml.training.mode', 'startup'),
            min_samples=self.get('ml.training.min_samples', 50),
            max_samples=self.get('ml.training.max_samples', 500)
        )
    
    def get_resource_config(self) -> ResourceConfig:
        """Get resource configuration"""
        return ResourceConfig(
            max_memory_mb=self.get('resources.max_memory_mb', 900),
            max_cpu_percent=self.get('resources.max_cpu_percent', 80),
            disk_space_mb=self.get('resources.disk_space_mb', 1024),
            max_processes=self.get('resources.max_processes', 50)
        )
    
    def is_aws_ec2(self) -> bool:
        """Check if running on AWS EC2"""
        return self.environment == 'AWS_EC2'
    
    def is_local(self) -> bool:
        """Check if running locally"""
        return self.environment == 'LOCAL'
    
    def get_enabled_features(self) -> list:
        """Get list of enabled ML features"""
        return self.get('ml.features.enabled', [
            'cpu_current', 'memory_current', 'error_rate',
            'response_time_avg', 'log_error_ratio'
        ])
    
    def get_disabled_features(self) -> list:
        """Get list of disabled ML features"""
        return self.get('ml.features.disabled', [])
    
    def validate_config(self) -> bool:
        """Validate configuration for t2.micro constraints"""
        try:
            # Check memory limits
            max_memory = self.get('resources.max_memory_mb', 900)
            if max_memory > 900:
                logger.error(f"Memory limit {max_memory}MB exceeds t2.micro recommendation of 900MB")
                return False
            
            # Check ML configuration
            n_estimators = self.get('ml.model.n_estimators', 50)
            if n_estimators > 100:
                logger.error(f"Too many estimators {n_estimators} for t2.micro, recommend <= 50")
                return False
            
            # Check polling intervals
            polling_interval = self.get('ml.inference.polling_interval', 60)
            if polling_interval < 30:
                logger.error(f"Polling interval {polling_interval}s too aggressive for t2.micro")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False

# Global configuration instance
config = ConfigManager()
