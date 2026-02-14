#!/usr/bin/env python3
"""
Optimized Flask Application for AWS t2.micro
Lightweight, memory-efficient, and production-ready
"""

import logging
import json
import time
import psutil
import threading
from datetime import datetime
from typing import Dict, Any
from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config
from monitoring.metrics_collector import MetricsCollector

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get('log_level', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/smart-incident-predictor/logs/application.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Global metrics collector (singleton pattern)
metrics_collector = MetricsCollector()
metrics_lock = threading.Lock()

class ResourceMonitor:
    """Monitor resource usage to stay within t2.micro limits"""
    
    def __init__(self):
        self.max_memory_mb = config.get('resources.max_memory_mb', 900)
        self.max_cpu_percent = config.get('resources.max_cpu_percent', 80)
        
    def check_resources(self) -> Dict[str, Any]:
        """Check if resources are within limits"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            memory_mb = memory.used / (1024 * 1024)
            memory_percent = memory.percent
            
            status = {
                'memory_mb': memory_mb,
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'within_limits': True,
                'warnings': []
            }
            
            # Check memory limits
            if memory_mb > self.max_memory_mb:
                status['within_limits'] = False
                status['warnings'].append(f"Memory {memory_mb:.0f}MB exceeds limit {self.max_memory_mb}MB")
            
            if memory_percent > 90:
                status['warnings'].append(f"Memory usage {memory_percent:.1f}% is critical")
            
            # Check CPU limits
            if cpu_percent > self.max_cpu_percent:
                status['warnings'].append(f"CPU usage {cpu_percent:.1f}% exceeds limit {self.max_cpu_percent}%")
            
            return status
            
        except Exception as e:
            logger.error(f"Resource check failed: {str(e)}")
            return {'within_limits': False, 'error': str(e)}
    
    def is_safe_to_proceed(self) -> bool:
        """Check if it's safe to continue operations"""
        status = self.check_resources()
        return status.get('within_limits', False)

resource_monitor = ResourceMonitor()

@app.before_request
def before_request():
    """Log incoming requests"""
    if config.get('development.log_all_requests', False):
        logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """Log responses and check resources"""
    if config.get('development.log_all_requests', False):
        logger.info(f"Response: {response.status_code}")
    
    # Check resources after each request
    if not resource_monitor.is_safe_to_proceed():
        logger.warning("Resource limits exceeded, consider scaling up")
    
    return response

@app.route('/')
def index():
    """Main endpoint - lightweight response"""
    try:
        return jsonify({
            'service': 'Smart Incident Predictor',
            'version': '1.0.0-t2micro',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': config.environment,
            'message': 'Lightweight predictive monitoring for AWS t2.micro'
        })
    except Exception as e:
        logger.error(f"Index endpoint error: {str(e)}")
        return jsonify({'error': 'Service unavailable'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint with resource monitoring"""
    try:
        # Check application health
        app_healthy = True
        app_status = "healthy"
        
        # Check resource health
        resource_status = resource_monitor.check_resources()
        
        # Overall health determination
        overall_healthy = app_healthy and resource_status.get('within_limits', False)
        
        if not overall_healthy:
            app_status = "unhealthy"
        
        response_data = {
            'status': app_status,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': time.time() - metrics_collector.start_time,
            'checks': {
                'application': 'ok' if app_healthy else 'critical',
                'memory': 'ok' if resource_status.get('memory_percent', 0) < 85 else 'warning',
                'cpu': 'ok' if resource_status.get('cpu_percent', 0) < 80 else 'warning'
            },
            'resources': {
                'memory_mb': resource_status.get('memory_mb', 0),
                'memory_percent': resource_status.get('memory_percent', 0),
                'cpu_percent': resource_status.get('cpu_percent', 0)
            },
            'warnings': resource_status.get('warnings', [])
        }
        
        status_code = 200 if overall_healthy else 503
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.route('/api/metrics')
def get_metrics():
    """Get system and application metrics"""
    try:
        # Check if safe to collect metrics
        if not resource_monitor.is_safe_to_proceed():
            return jsonify({
                'error': 'Resource limits exceeded, cannot collect metrics'
            }), 503
        
        # Collect system metrics (lightweight version)
        system_metrics = _collect_lightweight_metrics()
        
        # Collect application metrics
        app_metrics = {
            'uptime_seconds': time.time() - metrics_collector.start_time,
            'requests_per_minute': _estimate_rpm(),
            'error_rate': _estimate_error_rate(),
            'memory_usage_mb': psutil.Process().memory_info().rss / (1024 * 1024)
        }
        
        response_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': system_metrics,
            'application': app_metrics,
            'resource_status': resource_monitor.check_resources()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return jsonify({'error': 'Failed to collect metrics'}), 500

@app.route('/api/status')
def get_status():
    """Get detailed system status"""
    try:
        # Get resource status
        resource_status = resource_monitor.check_resources()
        
        # Get ML service status (check if process is running)
        ml_status = _check_ml_service_status()
        
        response_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': config.environment,
            'services': {
                'api': {
                    'status': 'running',
                    'port': config.get('app.port', 5000),
                    'memory_mb': psutil.Process().memory_info().rss / (1024 * 1024)
                },
                'ml_detector': ml_status
            },
            'resources': resource_status,
            'configuration': {
                'max_memory_mb': config.get('resources.max_memory_mb'),
                'max_cpu_percent': config.get('resources.max_cpu_percent'),
                'ml_polling_interval': config.get('ml.inference.polling_interval'),
                'enabled_features': config.get_enabled_features()[:5]  # Show first 5
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500

@app.route('/api/config')
def get_config():
    """Get current configuration (safe subset)"""
    try:
        safe_config = {
            'environment': config.environment,
            'ml': {
                'algorithm': config.get('ml.model.algorithm'),
                'polling_interval': config.get('ml.inference.polling_interval'),
                'feature_limit': config.get('ml.inference.feature_limit'),
                'enabled_features': config.get_enabled_features()
            },
            'resources': {
                'max_memory_mb': config.get('resources.max_memory_mb'),
                'max_cpu_percent': config.get('resources.max_cpu_percent')
            },
            'app': {
                'port': config.get('app.port'),
                'workers': config.get('app.workers')
            }
        }
        
        return jsonify(safe_config)
        
    except Exception as e:
        logger.error(f"Config endpoint error: {str(e)}")
        return jsonify({'error': 'Failed to get configuration'}), 500

def _collect_lightweight_metrics() -> Dict[str, Any]:
    """Collect essential metrics with minimal resource usage"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics (root partition only)
        disk = psutil.disk_usage('/')
        
        # Network metrics (simplified)
        network = psutil.net_io_counters()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'disk_percent': (disk.used / disk.total) * 100,
            'disk_free_gb': disk.free / (1024 * 1024 * 1024),
            'network_bytes_sent': network.bytes_sent,
            'network_bytes_recv': network.bytes_recv
        }
        
    except Exception as e:
        logger.error(f"Lightweight metrics collection failed: {str(e)}")
        return {}

def _estimate_rpm() -> int:
    """Estimate requests per minute (simplified)"""
    # This would be implemented with a proper request counter in production
    return 50  # Placeholder

def _estimate_error_rate() -> float:
    """Estimate error rate (simplified)"""
    # This would be implemented with proper error tracking in production
    return 1.5  # Placeholder

def _check_ml_service_status() -> Dict[str, Any]:
    """Check if ML service is running"""
    try:
        # Check if ML service process is running
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'anomaly_detector.py' in cmdline:
                    return {
                        'status': 'running',
                        'pid': proc.info['pid'],
                        'memory_mb': proc.memory_info().rss / (1024 * 1024)
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            'status': 'not_running',
            'message': 'ML anomaly detector service not found'
        }
        
    except Exception as e:
        logger.error(f"ML service status check failed: {str(e)}")
        return {
            'status': 'unknown',
            'error': str(e)
        }

def create_app():
    """Application factory"""
    logger.info("Creating optimized Flask application for t2.micro")
    
    # Validate configuration
    if not config.validate_config():
        logger.error("Configuration validation failed")
        raise RuntimeError("Invalid configuration for t2.micro deployment")
    
    logger.info(f"Application configured for {config.environment} environment")
    logger.info(f"Memory limit: {config.get('resources.max_memory_mb')}MB")
    logger.info(f"ML polling interval: {config.get('ml.inference.polling_interval')}s")
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    app_config = config.get_app_config()
    
    logger.info(f"Starting optimized application on {app_config.host}:{app_config.port}")
    logger.info(f"Debug mode: {app_config.debug}")
    
    app.run(
        host=app_config.host,
        port=app_config.port,
        debug=app_config.debug,
        threaded=True,
        use_reloader=False  # Important for production
    )
