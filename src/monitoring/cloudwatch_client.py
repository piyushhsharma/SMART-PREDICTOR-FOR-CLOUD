#!/usr/bin/env python3
"""
CloudWatch Client
Handles data collection from AWS CloudWatch
"""

import logging
import boto3
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CloudWatchClient:
    """Client for interacting with AWS CloudWatch"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.logs = boto3.client('logs')
        
        # Configuration
        self.config = {
            'instance_id': self._get_instance_id(),
            'region': self._get_region(),
            'log_group_names': [
                '/aws/ec2/smart-incident-predictor/application',
                '/aws/ec2/smart-incident-predictor/ml-service'
            ]
        }
        
        logger.info(f"CloudWatch client initialized for instance {self.config['instance_id']}")
    
    def get_recent_metrics(self, window_minutes: int = 5) -> Dict:
        """Get recent metrics from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=window_minutes)
            
            metrics = {}
            
            # Define metrics to collect
            metric_queries = [
                # CPU Utilization
                {
                    'Id': 'cpu_utilization',
                    'Label': 'CPUUtilization',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'CPUUtilization',
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': self.config['instance_id']}
                            ]
                        },
                        'Period': 60,  # 1 minute
                        'Stat': 'Average'
                    }
                },
                # Memory Utilization (custom metric)
                {
                    'Id': 'memory_utilization',
                    'Label': 'MemoryUtilization',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'System/Linux',
                            'MetricName': 'MemoryUtilization',
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': self.config['instance_id']}
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Average'
                    }
                },
                # Disk Utilization
                {
                    'Id': 'disk_utilization',
                    'Label': 'DiskSpaceUtilization',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'System/Linux',
                            'MetricName': 'DiskSpaceUtilization',
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': self.config['instance_id']},
                                {'Name': 'Path', 'Value': '/'}
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Average'
                    }
                },
                # Network In
                {
                    'Id': 'network_in',
                    'Label': 'NetworkIn',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'NetworkIn',
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': self.config['instance_id']}
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Sum'
                    }
                },
                # Network Out
                {
                    'Id': 'network_out',
                    'Label': 'NetworkOut',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'NetworkOut',
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': self.config['instance_id']}
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Sum'
                    }
                }
            ]
            
            # Get metrics
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time
            )
            
            # Process results
            for result in response['MetricDataResults']:
                metric_name = result['Label'].lower().replace(' ', '_')
                values = result['Values']
                
                if values:
                    metrics[metric_name] = values
                else:
                    # Fallback to simulated data if no real data
                    metrics[metric_name] = self._simulate_metric_data(metric_name, window_minutes)
            
            # Add derived metrics
            metrics.update(self._calculate_derived_metrics(metrics))
            
            logger.debug(f"Retrieved {len(metrics)} metrics from CloudWatch")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics from CloudWatch: {str(e)}")
            return self._get_fallback_metrics(window_minutes)
    
    def get_log_patterns(self, window_minutes: int = 5) -> List[Dict]:
        """Get log patterns from CloudWatch Logs"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=window_minutes)
            
            all_logs = []
            
            for log_group_name in self.config['log_group_names']:
                try:
                    logs = self._get_logs_from_group(
                        log_group_name, start_time, end_time
                    )
                    all_logs.extend(logs)
                except Exception as e:
                    logger.warning(f"Failed to get logs from {log_group_name}: {str(e)}")
            
            # Parse log entries
            parsed_logs = []
            for log_entry in all_logs:
                parsed = self._parse_log_entry(log_entry)
                if parsed:
                    parsed_logs.append(parsed)
            
            logger.debug(f"Retrieved {len(parsed_logs)} log entries")
            return parsed_logs
            
        except Exception as e:
            logger.error(f"Failed to get log patterns: {str(e)}")
            return []
    
    def put_custom_metric(self, metric_name: str, value: float, unit: str = 'None'):
        """Put custom metric to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='Custom/ML',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': self.config['instance_id']
                            }
                        ]
                    }
                ]
            )
            
            logger.debug(f"Put custom metric {metric_name}: {value}")
            
        except Exception as e:
            logger.error(f"Failed to put custom metric {metric_name}: {str(e)}")
    
    def _get_logs_from_group(self, log_group_name: str, start_time: datetime, end_time: datetime) -> List[str]:
        """Get logs from a specific log group"""
        try:
            # Get log streams
            log_streams = self.logs.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=5
            )
            
            all_log_events = []
            
            for stream in log_streams.get('logStreams', []):
                stream_name = stream['logStreamName']
                
                # Get log events
                events = self.logs.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=stream_name,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000),
                    limit=100
                )
                
                all_log_events.extend(events.get('events', []))
            
            # Extract messages
            log_messages = [event['message'] for event in all_log_events]
            return log_messages
            
        except Exception as e:
            logger.error(f"Failed to get logs from {log_group_name}: {str(e)}")
            return []
    
    def _parse_log_entry(self, log_message: str) -> Optional[Dict]:
        """Parse a single log entry"""
        try:
            # Try to parse as JSON first
            if log_message.strip().startswith('{'):
                try:
                    parsed = json.loads(log_message)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
            
            # Parse as structured log
            parsed = {
                'message': log_message,
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'INFO'
            }
            
            # Extract log level
            level_patterns = [
                (r'\b(ERROR|FATAL|CRITICAL)\b', 'ERROR'),
                (r'\b(WARNING|WARN)\b', 'WARNING'),
                (r'\b(INFO|INFORMATION)\b', 'INFO'),
                (r'\b(DEBUG)\b', 'DEBUG')
            ]
            
            for pattern, level in level_patterns:
                if re.search(pattern, log_message, re.IGNORECASE):
                    parsed['level'] = level
                    break
            
            # Extract response time if present
            rt_match = re.search(r'response_time[_]?ms[:\s]+(\d+\.?\d*)', log_message, re.IGNORECASE)
            if rt_match:
                parsed['response_time_ms'] = float(rt_match.group(1))
            
            # Extract error type if present
            error_match = re.search(r'error[_]?type[:\s]+([A-Za-z0-9_]+)', log_message, re.IGNORECASE)
            if error_match:
                parsed['error_type'] = error_match.group(1)
            
            return parsed
            
        except Exception as e:
            logger.debug(f"Failed to parse log entry: {str(e)}")
            return None
    
    def _calculate_derived_metrics(self, metrics: Dict) -> Dict:
        """Calculate derived metrics from base metrics"""
        derived = {}
        
        try:
            # Network I/O
            if 'network_in' in metrics and 'network_out' in metrics:
                network_in = metrics['network_in']
                network_out = metrics['network_out']
                
                if network_in and network_out:
                    derived['network_io'] = {
                        'bytes_sent': network_out,
                        'bytes_received': network_in
                    }
            
            # Calculate request count (simulated based on network activity)
            if 'network_in' in metrics:
                network_in = metrics['network_in']
                if network_in:
                    # Rough estimate: each request ~1KB
                    derived['request_count'] = [max(1, int(bytes_in / 1024)) for bytes_in in network_in]
            
            # Calculate error rate (simulated)
            if 'cpu_utilization' in metrics:
                cpu_data = metrics['cpu_utilization']
                if cpu_data:
                    # Simulate error rate based on CPU usage
                    derived['error_rate'] = [
                        max(0, min(20, (cpu - 50) * 0.4)) for cpu in cpu_data
                    ]
            
            # Calculate response time (simulated)
            if 'cpu_utilization' in metrics:
                cpu_data = metrics['cpu_utilization']
                if cpu_data:
                    # Simulate response time based on CPU usage
                    derived['response_time'] = [
                        max(100, 100 + (cpu - 30) * 10) for cpu in cpu_data
                    ]
            
        except Exception as e:
            logger.error(f"Failed to calculate derived metrics: {str(e)}")
        
        return derived
    
    def _simulate_metric_data(self, metric_name: str, window_minutes: int) -> List[float]:
        """Simulate metric data when real data is not available"""
        import random
        
        data_points = window_minutes  # One per minute
        
        if 'cpu' in metric_name:
            # CPU simulation with occasional spikes
            base_cpu = random.uniform(20, 40)
            return [
                max(0, min(100, base_cpu + random.uniform(-10, 20)))
                for _ in range(data_points)
            ]
        
        elif 'memory' in metric_name:
            # Memory simulation (more stable)
            base_memory = random.uniform(50, 70)
            return [
                max(0, min(100, base_memory + random.uniform(-5, 10)))
                for _ in range(data_points)
            ]
        
        elif 'disk' in metric_name:
            # Disk simulation (very stable)
            base_disk = random.uniform(30, 50)
            return [
                max(0, min(100, base_disk + random.uniform(-2, 5)))
                for _ in range(data_points)
            ]
        
        elif 'network' in metric_name:
            # Network simulation with variability
            base_network = random.uniform(1000, 5000)
            return [
                max(0, base_network + random.uniform(-500, 2000))
                for _ in range(data_points)
            ]
        
        else:
            # Default simulation
            return [random.uniform(0, 100) for _ in range(data_points)]
    
    def _get_fallback_metrics(self, window_minutes: int) -> Dict:
        """Get fallback metrics when CloudWatch is not available"""
        logger.warning("Using fallback metrics (simulated data)")
        
        metrics = {}
        
        # Simulate all standard metrics
        metric_names = [
            'cpu_utilization', 'memory_utilization', 'disk_utilization',
            'network_in', 'network_out'
        ]
        
        for metric_name in metric_names:
            metrics[metric_name] = self._simulate_metric_data(metric_name, window_minutes)
        
        # Add derived metrics
        metrics.update(self._calculate_derived_metrics(metrics))
        
        return metrics
    
    def _get_instance_id(self) -> str:
        """Get EC2 instance ID"""
        try:
            import requests
            response = requests.get('http://169.254.169.254/latest/meta-data/instance-id', timeout=2)
            return response.text
        except Exception:
            return 'i-unknown'
    
    def _get_region(self) -> str:
        """Get AWS region"""
        try:
            import requests
            response = requests.get('http://169.254.169.254/latest/meta-data/placement/region', timeout=2)
            return response.text
        except Exception:
            return 'us-east-1'
