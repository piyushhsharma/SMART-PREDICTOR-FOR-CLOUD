#!/usr/bin/env python3
"""
Sample Cloud Application
Simulates a production-like web application with various log patterns
"""

import time
import random
import logging
import psutil
import json
from datetime import datetime
from flask import Flask, jsonify, request
from log_generator import LogGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/smart-incident-predictor/logs/application.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
log_generator = LogGenerator()

class ApplicationMetrics:
    """Collect application and system metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_metrics(self):
        """Get system-level metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'network_io': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv
            }
        }
    
    def get_application_metrics(self):
        """Get application-level metrics"""
        uptime = time.time() - self.start_time
        return {
            'uptime_seconds': uptime,
            'requests_per_minute': self._calculate_rpm(),
            'error_rate': self._calculate_error_rate(),
            'response_time_avg': self._calculate_avg_response_time()
        }
    
    def _calculate_rpm(self):
        """Calculate requests per minute (simulated)"""
        return random.randint(50, 200)
    
    def _calculate_error_rate(self):
        """Calculate error rate (simulated)"""
        # Simulate occasional error spikes
        if random.random() < 0.05:  # 5% chance of error spike
            return random.uniform(10, 25)
        return random.uniform(0.5, 3.0)
    
    def _calculate_avg_response_time(self):
        """Calculate average response time (simulated)"""
        # Simulate occasional latency spikes
        if random.random() < 0.03:  # 3% chance of latency spike
            return random.uniform(800, 2000)
        return random.uniform(100, 400)

metrics = ApplicationMetrics()

@app.route('/')
def index():
    """Main endpoint"""
    start_time = time.time()
    
    # Simulate processing time
    time.sleep(random.uniform(0.01, 0.1))
    
    # Generate normal log
    log_generator.generate_normal_log(
        endpoint='/',
        method='GET',
        status_code=200,
        response_time=(time.time() - start_time) * 1000
    )
    
    return jsonify({
        'message': 'Smart Incident Predictor - Sample Application',
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy'
    })

@app.route('/api/users')
def get_users():
    """Users endpoint - can generate various response patterns"""
    start_time = time.time()
    
    # Simulate different scenarios
    scenario = random.random()
    
    if scenario < 0.02:  # 2% chance of server error
        log_generator.generate_error_log(
            endpoint='/api/users',
            method='GET',
            error_type='DatabaseConnectionError',
            error_message='Failed to connect to database'
        )
        return jsonify({'error': 'Internal server error'}), 500
    
    elif scenario < 0.05:  # 3% chance of slow response
        time.sleep(random.uniform(1.0, 2.0))
        log_generator.generate_warning_log(
            endpoint='/api/users',
            method='GET',
            warning_type='SlowQuery',
            response_time=(time.time() - start_time) * 1000
        )
    else:
        # Normal response
        time.sleep(random.uniform(0.05, 0.2))
        log_generator.generate_normal_log(
            endpoint='/api/users',
            method='GET',
            status_code=200,
            response_time=(time.time() - start_time) * 1000
        )
    
    return jsonify({
        'users': [
            {'id': 1, 'name': 'John Doe'},
            {'id': 2, 'name': 'Jane Smith'}
        ],
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Orders endpoint - POST request simulation"""
    start_time = time.time()
    
    try:
        # Simulate order processing
        time.sleep(random.uniform(0.1, 0.3))
        
        # Random failure scenarios
        scenario = random.random()
        
        if scenario < 0.03:  # 3% chance of validation error
            log_generator.generate_error_log(
                endpoint='/api/orders',
                method='POST',
                error_type='ValidationError',
                error_message='Invalid order data'
            )
            return jsonify({'error': 'Invalid order data'}), 400
        
        elif scenario < 0.05:  # 2% chance of payment processing error
            log_generator.generate_error_log(
                endpoint='/api/orders',
                method='POST',
                error_type='PaymentError',
                error_message='Payment processing failed'
            )
            return jsonify({'error': 'Payment failed'}), 502
        
        # Success case
        log_generator.generate_normal_log(
            endpoint='/api/orders',
            method='POST',
            status_code=201,
            response_time=(time.time() - start_time) * 1000
        )
        
        return jsonify({
            'order_id': random.randint(1000, 9999),
            'status': 'created',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        log_generator.generate_error_log(
            endpoint='/api/orders',
            method='POST',
            error_type='UnexpectedError',
            error_message=str(e)
        )
        return jsonify({'error': 'Unexpected error occurred'}), 500

@app.route('/api/metrics')
def get_metrics():
    """Metrics endpoint for monitoring"""
    try:
        system_metrics = metrics.get_system_metrics()
        app_metrics = metrics.get_application_metrics()
        
        # Log metrics collection
        logger.info(f"Metrics collected - CPU: {system_metrics['cpu_percent']}%, "
                   f"Memory: {system_metrics['memory_percent']}%, "
                   f"Error Rate: {app_metrics['error_rate']}%")
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'system': system_metrics,
            'application': app_metrics
        })
        
    except Exception as e:
        logger.error(f"Failed to collect metrics: {str(e)}")
        return jsonify({'error': 'Failed to collect metrics'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        system_metrics = metrics.get_system_metrics()
        
        # Determine health status
        cpu_ok = system_metrics['cpu_percent'] < 90
        memory_ok = system_metrics['memory_percent'] < 90
        disk_ok = system_metrics['disk_percent'] < 90
        
        status = 'healthy' if all([cpu_ok, memory_ok, disk_ok]) else 'unhealthy'
        http_status = 200 if status == 'healthy' else 503
        
        return jsonify({
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'cpu': 'ok' if cpu_ok else 'critical',
                'memory': 'ok' if memory_ok else 'critical',
                'disk': 'ok' if disk_ok else 'critical'
            }
        }), http_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

def simulate_background_activity():
    """Simulate background application activity"""
    while True:
        try:
            # Generate random background logs
            scenario = random.random()
            
            if scenario < 0.1:  # 10% chance of background task log
                log_generator.generate_background_log()
            
            elif scenario < 0.12:  # 2% chance of warning
                log_generator.generate_warning_log(
                    endpoint='/background/task',
                    method='INTERNAL',
                    warning_type='ResourceWarning',
                    response_time=random.uniform(500, 1500)
                )
            
            time.sleep(random.uniform(5, 15))
            
        except Exception as e:
            logger.error(f"Background activity error: {str(e)}")
            time.sleep(5)

if __name__ == '__main__':
    import threading
    
    # Start background activity thread
    background_thread = threading.Thread(target=simulate_background_activity, daemon=True)
    background_thread.start()
    
    logger.info("Starting Smart Incident Predictor Sample Application")
    
    # Start Flask application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
