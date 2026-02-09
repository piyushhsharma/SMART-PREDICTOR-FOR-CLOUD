#!/usr/bin/env python3
"""
Feature Extractor for Anomaly Detection
Extracts meaningful features from system metrics and logs
"""

import logging
import re
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extracts features from metrics and logs for ML analysis"""
    
    def __init__(self):
        self.log_patterns = {
            'error': re.compile(r'\b(ERROR|FATAL|CRITICAL)\b', re.IGNORECASE),
            'warning': re.compile(r'\b(WARNING|WARN)\b', re.IGNORECASE),
            'timeout': re.compile(r'\b(timeout|timed out)\b', re.IGNORECASE),
            'connection': re.compile(r'\b(connection|connect)\b', re.IGNORECASE),
            'memory': re.compile(r'\b(memory|out of memory|oom)\b', re.IGNORECASE),
            'database': re.compile(r'\b(database|db|sql)\b', re.IGNORECASE),
            'slow': re.compile(r'\b(slow|latency|delay)\b', re.IGNORECASE)
        }
        
        # Feature configuration
        self.feature_config = {
            'time_windows': [60, 300, 900],  # 1min, 5min, 15min in seconds
            'percentiles': [50, 90, 95, 99],
            'log_analysis_window': 300  # 5 minutes
        }
    
    def extract_features(self, metrics: Dict, logs: List[Dict]) -> Dict:
        """Extract comprehensive features from metrics and logs"""
        try:
            features = {}
            
            # Extract metric features
            metric_features = self._extract_metric_features(metrics)
            features.update(metric_features)
            
            # Extract log features
            log_features = self._extract_log_features(logs)
            features.update(log_features)
            
            # Extract combined features
            combined_features = self._extract_combined_features(metrics, logs)
            features.update(combined_features)
            
            # Add timestamp
            features['timestamp'] = datetime.utcnow().isoformat()
            
            logger.debug(f"Extracted {len(features)} features")
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract features: {str(e)}")
            return {}
    
    def _extract_metric_features(self, metrics: Dict) -> Dict:
        """Extract features from system metrics"""
        features = {}
        
        try:
            if not metrics:
                return self._get_default_metric_features()
            
            # CPU features
            if 'cpu_utilization' in metrics:
                cpu_data = metrics['cpu_utilization']
                features.update(self._extract_time_series_features(
                    cpu_data, 'cpu'
                ))
                
                # CPU-specific features
                features['cpu_current'] = cpu_data[-1] if cpu_data else 0
                features['cpu_trend'] = self._calculate_trend(cpu_data)
                features['cpu_volatility'] = np.std(cpu_data) if len(cpu_data) > 1 else 0
            
            # Memory features
            if 'memory_utilization' in metrics:
                mem_data = metrics['memory_utilization']
                features.update(self._extract_time_series_features(
                    mem_data, 'memory'
                ))
                
                features['memory_current'] = mem_data[-1] if mem_data else 0
                features['memory_trend'] = self._calculate_trend(mem_data)
            
            # Disk features
            if 'disk_utilization' in metrics:
                disk_data = metrics['disk_utilization']
                features.update(self._extract_time_series_features(
                    disk_data, 'disk'
                ))
                
                features['disk_current'] = disk_data[-1] if disk_data else 0
            
            # Network features
            if 'network_io' in metrics:
                net_data = metrics['network_io']
                features.update(self._extract_network_features(net_data))
            
            # Request metrics
            if 'request_count' in metrics:
                req_data = metrics['request_count']
                features.update(self._extract_request_features(req_data))
            
            # Response time features
            if 'response_time' in metrics:
                rt_data = metrics['response_time']
                features.update(self._extract_response_time_features(rt_data))
            
            # Error rate features
            if 'error_rate' in metrics:
                error_data = metrics['error_rate']
                features.update(self._extract_error_rate_features(error_data))
            
        except Exception as e:
            logger.error(f"Failed to extract metric features: {str(e)}")
            return self._get_default_metric_features()
        
        return features
    
    def _extract_log_features(self, logs: List[Dict]) -> Dict:
        """Extract features from log data"""
        features = {}
        
        try:
            if not logs:
                return self._get_default_log_features()
            
            # Log volume features
            features['log_count_total'] = len(logs)
            features['log_rate_per_minute'] = len(logs) / 5  # Assuming 5-minute window
            
            # Log level distribution
            log_levels = [log.get('level', 'INFO').upper() for log in logs]
            level_counts = Counter(log_levels)
            
            total_logs = len(logs)
            if total_logs > 0:
                features['log_error_ratio'] = level_counts.get('ERROR', 0) / total_logs
                features['log_warning_ratio'] = level_counts.get('WARNING', 0) / total_logs
                features['log_info_ratio'] = level_counts.get('INFO', 0) / total_logs
            else:
                features['log_error_ratio'] = 0
                features['log_warning_ratio'] = 0
                features['log_info_ratio'] = 0
            
            # Pattern matching features
            pattern_counts = defaultdict(int)
            for log in logs:
                message = log.get('message', '')
                for pattern_name, pattern in self.log_patterns.items():
                    if pattern.search(message):
                        pattern_counts[pattern_name] += 1
            
            # Pattern ratios
            if total_logs > 0:
                for pattern_name in self.log_patterns.keys():
                    features[f'log_pattern_{pattern_name}_ratio'] = (
                        pattern_counts[pattern_name] / total_logs
                    )
            
            # Error pattern analysis
            error_logs = [log for log in logs if log.get('level') == 'ERROR']
            if error_logs:
                features['error_types_count'] = len(set(
                    log.get('error_type', 'unknown') for log in error_logs
                ))
                features['recent_error_spike'] = self._detect_error_spike(error_logs)
            
            # Response time from logs
            response_times = []
            for log in logs:
                rt = log.get('response_time_ms')
                if rt and isinstance(rt, (int, float)):
                    response_times.append(rt)
            
            if response_times:
                features['log_response_time_avg'] = np.mean(response_times)
                features['log_response_time_p95'] = np.percentile(response_times, 95)
                features['log_response_time_max'] = np.max(response_times)
            else:
                features['log_response_time_avg'] = 0
                features['log_response_time_p95'] = 0
                features['log_response_time_max'] = 0
            
        except Exception as e:
            logger.error(f"Failed to extract log features: {str(e)}")
            return self._get_default_log_features()
        
        return features
    
    def _extract_combined_features(self, metrics: Dict, logs: List[Dict]) -> Dict:
        """Extract features that combine metrics and logs"""
        features = {}
        
        try:
            # Correlation between CPU and error rate
            if 'cpu_utilization' in metrics and 'error_rate' in metrics:
                cpu_data = metrics['cpu_utilization']
                error_data = metrics['error_rate']
                
                if len(cpu_data) > 1 and len(error_data) > 1:
                    correlation = np.corrcoef(cpu_data, error_data)[0, 1]
                    features['cpu_error_correlation'] = correlation if not np.isnan(correlation) else 0
                else:
                    features['cpu_error_correlation'] = 0
            
            # System stress score
            stress_factors = []
            
            # CPU stress
            if 'cpu_current' in features:
                stress_factors.append(features['cpu_current'] / 100)
            
            # Memory stress
            if 'memory_current' in features:
                stress_factors.append(features['memory_current'] / 100)
            
            # Error rate stress
            if 'log_error_ratio' in features:
                stress_factors.append(min(features['log_error_ratio'] * 10, 1))  # Scale error ratio
            
            if stress_factors:
                features['system_stress_score'] = np.mean(stress_factors)
            else:
                features['system_stress_score'] = 0
            
            # Anomaly likelihood (heuristic)
            anomaly_indicators = []
            
            # High CPU usage
            if features.get('cpu_current', 0) > 80:
                anomaly_indicators.append(1)
            
            # High memory usage
            if features.get('memory_current', 0) > 85:
                anomaly_indicators.append(1)
            
            # High error rate
            if features.get('log_error_ratio', 0) > 0.1:
                anomaly_indicators.append(1)
            
            # Slow response times
            if features.get('log_response_time_p95', 0) > 1000:
                anomaly_indicators.append(1)
            
            features['anomaly_likelihood'] = sum(anomaly_indicators) / max(len(anomaly_indicators), 1)
            
        except Exception as e:
            logger.error(f"Failed to extract combined features: {str(e)}")
        
        return features
    
    def _extract_time_series_features(self, data: List[float], prefix: str) -> Dict:
        """Extract statistical features from time series data"""
        features = {}
        
        if not data:
            return features
        
        try:
            # Basic statistics
            features[f'{prefix}_mean'] = np.mean(data)
            features[f'{prefix}_std'] = np.std(data)
            features[f'{prefix}_min'] = np.min(data)
            features[f'{prefix}_max'] = np.max(data)
            
            # Percentiles
            for p in self.feature_config['percentiles']:
                features[f'{prefix}_p{p}'] = np.percentile(data, p)
            
            # Recent vs historical comparison
            if len(data) >= 10:
                recent_data = data[-5:]  # Last 5 points
                historical_data = data[:-5]  # Everything before
                
                features[f'{prefix}_recent_avg'] = np.mean(recent_data)
                features[f'{prefix}_historical_avg'] = np.mean(historical_data)
                features[f'{prefix}_trend_ratio'] = (
                    features[f'{prefix}_recent_avg'] / 
                    max(features[f'{prefix}_historical_avg'], 1)
                )
            
        except Exception as e:
            logger.error(f"Failed to extract time series features for {prefix}: {str(e)}")
        
        return features
    
    def _extract_network_features(self, net_data: Dict) -> Dict:
        """Extract network-related features"""
        features = {}
        
        try:
            if 'bytes_sent' in net_data and 'bytes_received' in net_data:
                sent = net_data['bytes_sent']
                received = net_data['bytes_received']
                
                if isinstance(sent, list) and isinstance(received, list):
                    features['network_bytes_sent_current'] = sent[-1] if sent else 0
                    features['network_bytes_received_current'] = received[-1] if received else 0
                    
                    if len(sent) > 1:
                        features['network_bytes_sent_rate'] = sent[-1] - sent[-2]
                    if len(received) > 1:
                        features['network_bytes_received_rate'] = received[-1] - received[-2]
            
        except Exception as e:
            logger.error(f"Failed to extract network features: {str(e)}")
        
        return features
    
    def _extract_request_features(self, req_data: List[float]) -> Dict:
        """Extract request-related features"""
        features = {}
        
        try:
            if req_data:
                features['requests_current'] = req_data[-1] if req_data else 0
                features['requests_avg'] = np.mean(req_data)
                features['requests_peak'] = np.max(req_data)
                
                # Request trend
                if len(req_data) >= 5:
                    recent = np.mean(req_data[-3:])
                    historical = np.mean(req_data[:-3])
                    features['requests_trend'] = recent / max(historical, 1)
        
        except Exception as e:
            logger.error(f"Failed to extract request features: {str(e)}")
        
        return features
    
    def _extract_response_time_features(self, rt_data: List[float]) -> Dict:
        """Extract response time features"""
        features = {}
        
        try:
            if rt_data:
                features['response_time_current'] = rt_data[-1] if rt_data else 0
                features['response_time_avg'] = np.mean(rt_data)
                features['response_time_p95'] = np.percentile(rt_data, 95)
                features['response_time_max'] = np.max(rt_data)
                
                # Slow request ratio
                slow_threshold = 1000  # 1 second
                slow_requests = sum(1 for rt in rt_data if rt > slow_threshold)
                features['slow_requests_ratio'] = slow_requests / len(rt_data)
        
        except Exception as e:
            logger.error(f"Failed to extract response time features: {str(e)}")
        
        return features
    
    def _extract_error_rate_features(self, error_data: List[float]) -> Dict:
        """Extract error rate features"""
        features = {}
        
        try:
            if error_data:
                features['error_rate_current'] = error_data[-1] if error_data else 0
                features['error_rate_avg'] = np.mean(error_data)
                features['error_rate_max'] = np.max(error_data)
                
                # Error spike detection
                if len(error_data) >= 3:
                    recent_avg = np.mean(error_data[-3:])
                    historical_avg = np.mean(error_data[:-3])
                    features['error_spike_ratio'] = recent_avg / max(historical_avg, 0.1)
        
        except Exception as e:
            logger.error(f"Failed to extract error rate features: {str(e)}")
        
        return features
    
    def _calculate_trend(self, data: List[float]) -> float:
        """Calculate linear trend of time series"""
        try:
            if len(data) < 2:
                return 0
            
            x = np.arange(len(data))
            y = np.array(data)
            
            # Simple linear regression
            slope = np.polyfit(x, y, 1)[0]
            return slope
        
        except Exception:
            return 0
    
    def _detect_error_spike(self, error_logs: List[Dict]) -> float:
        """Detect if there's a recent spike in errors"""
        try:
            if len(error_logs) < 2:
                return 0
            
            # Group errors by minute
            error_counts = defaultdict(int)
            for log in error_logs:
                timestamp = log.get('timestamp', '')
                if timestamp:
                    # Extract minute from timestamp
                    minute_key = timestamp[:16]  # YYYY-MM-DDTHH:MM
                    error_counts[minute_key] += 1
            
            if len(error_counts) < 2:
                return 0
            
            # Compare recent minute to previous minute
            minutes = sorted(error_counts.keys())
            recent_count = error_counts[minutes[-1]]
            previous_count = error_counts[minutes[-2]] if len(minutes) > 1 else 1
            
            spike_ratio = recent_count / max(previous_count, 1)
            return min(spike_ratio, 10)  # Cap at 10x
        
        except Exception:
            return 0
    
    def _get_default_metric_features(self) -> Dict:
        """Return default metric features when no data available"""
        return {
            'cpu_current': 0,
            'cpu_mean': 0,
            'cpu_trend': 0,
            'memory_current': 0,
            'memory_mean': 0,
            'disk_current': 0,
            'system_stress_score': 0,
            'anomaly_likelihood': 0
        }
    
    def _get_default_log_features(self) -> Dict:
        """Return default log features when no data available"""
        return {
            'log_count_total': 0,
            'log_rate_per_minute': 0,
            'log_error_ratio': 0,
            'log_warning_ratio': 0,
            'log_info_ratio': 0,
            'error_types_count': 0,
            'recent_error_spike': 0
        }
