#!/usr/bin/env python3
"""
Log Generator for Sample Application
Simulates various log patterns that would be seen in production
"""

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class LogGenerator:
    """Generates realistic application logs for testing anomaly detection"""
    
    def __init__(self):
        self.logger = logging.getLogger('application')
        self.request_counter = 0
        self.error_patterns = [
            'DatabaseConnectionTimeout',
            'OutOfMemoryError',
            'NullPointerReference',
            'ServiceUnavailable',
            'RateLimitExceeded',
            'AuthenticationFailed',
            'ValidationError',
            'NetworkTimeout',
            'FileSystemError',
            'ConfigurationError'
        ]
        
        self.warning_patterns = [
            'SlowDatabaseQuery',
            'HighMemoryUsage',
            'DiskSpaceLow',
            'CacheMiss',
            'RetryingOperation',
            'DeprecatedAPI',
            'ResourceContention',
            'SlowResponseTime',
            'ConnectionPoolExhaustion',
            'GarbageCollectionPause'
        ]
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'curl/7.68.0',
            'Python-requests/2.28.1',
            'PostmanRuntime/7.29.2'
        ]
        
        self.ip_addresses = [
            '192.168.1.100', '10.0.0.50', '172.16.0.25',
            '203.0.113.1', '198.51.100.10', '192.0.2.100'
        ]
    
    def generate_normal_log(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Generate a normal application log entry"""
        self.request_counter += 1
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'request_id': f"req_{self.request_counter:06d}",
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time_ms': round(response_time, 2),
            'client_ip': random.choice(self.ip_addresses),
            'user_agent': random.choice(self.user_agents),
            'message': f"{method} {endpoint} - {status_code} - {response_time:.2f}ms"
        }
        
        self.logger.info(json_format(log_data))
    
    def generate_error_log(self, endpoint: str, method: str, error_type: str, error_message: str):
        """Generate an error log entry"""
        self.request_counter += 1
        
        # Simulate stack trace
        stack_trace = self._generate_stack_trace(error_type)
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'ERROR',
            'request_id': f"req_{self.request_counter:06d}",
            'method': method,
            'endpoint': endpoint,
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'client_ip': random.choice(self.ip_addresses),
            'message': f"ERROR in {method} {endpoint}: {error_type} - {error_message}"
        }
        
        self.logger.error(json_format(log_data))
    
    def generate_warning_log(self, endpoint: str, method: str, warning_type: str, response_time: float = None):
        """Generate a warning log entry"""
        self.request_counter += 1
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'WARNING',
            'request_id': f"req_{self.request_counter:06d}",
            'method': method,
            'endpoint': endpoint,
            'warning_type': warning_type,
            'response_time_ms': round(response_time, 2) if response_time else None,
            'client_ip': random.choice(self.ip_addresses),
            'message': f"WARNING in {method} {endpoint}: {warning_type}"
        }
        
        if response_time and response_time > 1000:
            log_data['performance_issue'] = 'slow_response'
        
        self.logger.warning(json_format(log_data))
    
    def generate_background_log(self):
        """Generate background task logs"""
        tasks = [
            'Database backup completed',
            'Cache refreshed successfully',
            'Session cleanup completed',
            'Metrics aggregation finished',
            'Health check passed',
            'Scheduled maintenance task completed'
        ]
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'component': 'background',
            'task': random.choice(tasks),
            'duration_ms': random.randint(100, 5000),
            'message': f"Background task: {random.choice(tasks)}"
        }
        
        self.logger.info(json_format(log_data))
    
    def generate_error_spike(self, count: int = 5):
        """Generate a spike of errors to simulate system issues"""
        error_type = random.choice(self.error_patterns)
        
        for i in range(count):
            self.generate_error_log(
                endpoint='/api/critical',
                method='GET',
                error_type=error_type,
                error_message=f'Simulated error spike #{i+1}'
            )
            time.sleep(random.uniform(0.1, 0.5))
    
    def generate_latency_spike(self, duration_seconds: int = 30):
        """Generate logs with high latency to simulate performance issues"""
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            self.generate_warning_log(
                endpoint='/api/slow',
                method='GET',
                warning_type='SlowResponseTime',
                response_time=random.uniform(1000, 3000)
            )
            time.sleep(random.uniform(1, 3))
    
    def _generate_stack_trace(self, error_type: str) -> str:
        """Generate a realistic stack trace"""
        stack_frames = [
            f'File "/opt/app/src/handlers.py", line 42, in process_request',
            f'File "/opt/app/src/services.py", line 128, in execute_operation',
            f'File "/opt/app/src/database.py", line 67, in query_database',
            f'File "/opt/app/src/utils.py", line 234, in validate_input'
        ]
        
        return f"{error_type}: Simulated error\n" + "\n".join(stack_frames)
    
    def simulate_traffic_pattern(self):
        """Simulate realistic traffic patterns throughout the day"""
        current_hour = datetime.now().hour
        
        # Traffic patterns based on time of day
        if 6 <= current_hour <= 9:  # Morning rush
            base_delay = 0.1
            error_probability = 0.02
        elif 10 <= current_hour <= 16:  # Business hours
            base_delay = 0.2
            error_probability = 0.015
        elif 17 <= current_hour <= 20:  # Evening rush
            base_delay = 0.15
            error_probability = 0.025
        else:  # Night hours
            base_delay = 0.5
            error_probability = 0.01
        
        # Simulate random requests
        while True:
            try:
                # Random delay between requests
                time.sleep(random.uniform(base_delay, base_delay * 3))
                
                # Random endpoint selection
                endpoints = [
                    ('/', 'GET'),
                    ('/api/users', 'GET'),
                    ('/api/orders', 'POST'),
                    ('/api/products', 'GET'),
                    ('/api/health', 'GET')
                ]
                
                endpoint, method = random.choice(endpoints)
                
                # Determine if this should be an error
                if random.random() < error_probability:
                    error_type = random.choice(self.error_patterns)
                    self.generate_error_log(
                        endpoint=endpoint,
                        method=method,
                        error_type=error_type,
                        error_message=f'Simulated {error_type}'
                    )
                else:
                    # Normal request
                    response_time = random.uniform(50, 300)
                    status_code = 200 if method == 'GET' else 201
                    
                    self.generate_normal_log(
                        endpoint=endpoint,
                        method=method,
                        status_code=status_code,
                        response_time=response_time
                    )
                    
            except Exception as e:
                self.logger.error(f"Traffic simulation error: {str(e)}")
                time.sleep(1)

def json_format(data: Dict[str, Any]) -> str:
    """Format dictionary as JSON string for logging"""
    import json
    return json.dumps(data, separators=(',', ':'))

# Example usage
if __name__ == '__main__':
    generator = LogGenerator()
    
    # Generate sample logs
    generator.generate_normal_log('/', 'GET', 200, 150.5)
    generator.generate_error_log('/api/users', 'GET', 'DatabaseError', 'Connection timeout')
    generator.generate_warning_log('/api/orders', 'POST', 'SlowQuery', 1250.0)
    generator.generate_background_log()
