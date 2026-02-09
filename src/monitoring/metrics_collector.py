#!/usr/bin/env python3
"""
Metrics Collector
Collects and aggregates system and application metrics
"""

import logging
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history = []
        self.collection_interval = 30  # seconds
        
        logger.info("Metrics Collector initialized")
    
    def collect_system_metrics(self) -> Dict:
        """Collect system-level metrics"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'cpu': self._get_cpu_metrics(),
                'memory': self._get_memory_metrics(),
                'disk': self._get_disk_metrics(),
                'network': self._get_network_metrics(),
                'processes': self._get_process_metrics()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")
            return {}
    
    def collect_application_metrics(self) -> Dict:
        """Collect application-level metrics"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': time.time() - self.start_time,
                'python_processes': self._get_python_metrics(),
                'file_descriptors': self._get_file_descriptor_metrics(),
                'connections': self._get_connection_metrics()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {str(e)}")
            return {}
    
    def _get_cpu_metrics(self) -> Dict:
        """Get CPU-related metrics"""
        try:
            # CPU usage percentages
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # CPU load averages (Linux only)
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            
            # CPU temperature (if available)
            cpu_temp = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            cpu_temp = entries[0].current
                            break
            except Exception:
                pass
            
            return {
                'usage_percent': cpu_percent,
                'usage_per_core': cpu_per_core,
                'load_average_1min': load_avg[0],
                'load_average_5min': load_avg[1],
                'load_average_15min': load_avg[2],
                'frequency_current_mhz': cpu_freq.current if cpu_freq else None,
                'frequency_min_mhz': cpu_freq.min if cpu_freq else None,
                'frequency_max_mhz': cpu_freq.max if cpu_freq else None,
                'temperature_celsius': cpu_temp
            }
            
        except Exception as e:
            logger.error(f"Failed to get CPU metrics: {str(e)}")
            return {}
    
    def _get_memory_metrics(self) -> Dict:
        """Get memory-related metrics"""
        try:
            # Virtual memory
            virtual_mem = psutil.virtual_memory()
            
            # Swap memory
            swap_mem = psutil.swap_memory()
            
            return {
                'virtual': {
                    'total_bytes': virtual_mem.total,
                    'available_bytes': virtual_mem.available,
                    'used_bytes': virtual_mem.used,
                    'free_bytes': virtual_mem.free,
                    'percent_used': virtual_mem.percent,
                    'active_bytes': getattr(virtual_mem, 'active', 0),
                    'inactive_bytes': getattr(virtual_mem, 'inactive', 0),
                    'buffers_bytes': getattr(virtual_mem, 'buffers', 0),
                    'cached_bytes': getattr(virtual_mem, 'cached', 0)
                },
                'swap': {
                    'total_bytes': swap_mem.total,
                    'used_bytes': swap_mem.used,
                    'free_bytes': swap_mem.free,
                    'percent_used': swap_mem.percent,
                    'sin_bytes': swap_mem.sin,
                    'sout_bytes': swap_mem.sout
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory metrics: {str(e)}")
            return {}
    
    def _get_disk_metrics(self) -> Dict:
        """Get disk-related metrics"""
        try:
            disk_metrics = {}
            
            # Disk usage for all partitions
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_metrics[partition.device] = {
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_bytes': usage.total,
                        'used_bytes': usage.used,
                        'free_bytes': usage.free,
                        'percent_used': (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    }
                except Exception:
                    continue
            
            # Disk I/O statistics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_metrics['io'] = {
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count,
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_time_ms': disk_io.read_time,
                    'write_time_ms': disk_io.write_time,
                    'read_merged_count': getattr(disk_io, 'read_merged_count', 0),
                    'write_merged_count': getattr(disk_io, 'write_merged_count', 0)
                }
            
            return disk_metrics
            
        except Exception as e:
            logger.error(f"Failed to get disk metrics: {str(e)}")
            return {}
    
    def _get_network_metrics(self) -> Dict:
        """Get network-related metrics"""
        try:
            network_metrics = {}
            
            # Network I/O statistics
            net_io = psutil.net_io_counters()
            if net_io:
                network_metrics['io'] = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                }
            
            # Network connections
            connections = psutil.net_connections()
            connection_stats = {
                'established': 0,
                'listen': 0,
                'time_wait': 0,
                'close_wait': 0,
                'total': len(connections)
            }
            
            for conn in connections:
                status = conn.status
                if status in connection_stats:
                    connection_stats[status] += 1
            
            network_metrics['connections'] = connection_stats
            
            # Network interfaces
            net_if_addrs = psutil.net_if_addrs()
            network_metrics['interfaces'] = {}
            
            for interface_name, addresses in net_if_addrs.items():
                interface_info = {
                    'addresses': []
                }
                
                for addr in addresses:
                    interface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                
                network_metrics['interfaces'][interface_name] = interface_info
            
            return network_metrics
            
        except Exception as e:
            logger.error(f"Failed to get network metrics: {str(e)}")
            return {}
    
    def _get_process_metrics(self) -> Dict:
        """Get process-related metrics"""
        try:
            # Total processes
            total_processes = len(psutil.pids())
            
            # Process counts by status
            process_counts = {}
            for proc in psutil.process_iter(['status']):
                try:
                    status = proc.info['status']
                    process_counts[status] = process_counts.get(status, 0) + 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Top CPU consuming processes
            top_cpu = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if proc.info['cpu_percent'] > 0:
                        top_cpu.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            top_cpu.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_cpu = top_cpu[:5]  # Top 5
            
            # Top memory consuming processes
            top_memory = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    if proc.info['memory_percent'] > 0:
                        top_memory.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            top_memory.sort(key=lambda x: x['memory_percent'], reverse=True)
            top_memory = top_memory[:5]  # Top 5
            
            return {
                'total_count': total_processes,
                'status_counts': process_counts,
                'top_cpu_consumers': top_cpu,
                'top_memory_consumers': top_memory
            }
            
        except Exception as e:
            logger.error(f"Failed to get process metrics: {str(e)}")
            return {}
    
    def _get_python_metrics(self) -> Dict:
        """Get Python-specific metrics"""
        try:
            import sys
            import gc
            
            # Current process
            current_process = psutil.Process()
            
            # Memory info for current process
            memory_info = current_process.memory_info()
            
            # GC stats
            gc_stats = gc.get_stats() if hasattr(gc, 'get_stats') else []
            
            return {
                'version': sys.version,
                'process_id': current_process.pid,
                'memory_rss_bytes': memory_info.rss,
                'memory_vms_bytes': memory_info.vms,
                'cpu_percent': current_process.cpu_percent(),
                'num_threads': current_process.num_threads(),
                'open_files': len(current_process.open_files()),
                'gc_stats': gc_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get Python metrics: {str(e)}")
            return {}
    
    def _get_file_descriptor_metrics(self) -> Dict:
        """Get file descriptor metrics"""
        try:
            import os
            
            # Current process
            current_process = psutil.Process()
            
            # Open file descriptors
            try:
                open_fds = current_process.num_fds()
            except AttributeError:
                # Windows doesn't have num_fds()
                open_fds = len(current_process.open_files())
            
            # System-wide file descriptor limits (Linux only)
            fd_limits = {}
            try:
                fd_limits['soft_limit'] = os.sysconf('SC_OPEN_MAX')
            except (AttributeError, OSError):
                pass
            
            return {
                'open_count': open_fds,
                'limits': fd_limits
            }
            
        except Exception as e:
            logger.error(f"Failed to get file descriptor metrics: {str(e)}")
            return {}
    
    def _get_connection_metrics(self) -> Dict:
        """Get connection metrics for the application"""
        try:
            current_process = psutil.Process()
            connections = current_process.connections()
            
            connection_stats = {
                'total': len(connections),
                'established': 0,
                'listen': 0,
                'time_wait': 0,
                'close_wait': 0
            }
            
            local_ports = []
            remote_addresses = []
            
            for conn in connections:
                status = conn.status
                if status in connection_stats:
                    connection_stats[status] += 1
                
                if conn.laddr:
                    local_ports.append(conn.laddr.port)
                
                if conn.raddr:
                    remote_addresses.append(f"{conn.raddr.ip}:{conn.raddr.port}")
            
            return {
                'stats': connection_stats,
                'local_ports': list(set(local_ports)),
                'remote_addresses': list(set(remote_addresses))
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection metrics: {str(e)}")
            return {}
    
    def store_metrics(self, metrics: Dict):
        """Store metrics in history"""
        try:
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 entries
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to store metrics: {str(e)}")
    
    def get_metrics_summary(self, minutes: int = 5) -> Dict:
        """Get summary of recent metrics"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')) > cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            # Calculate averages and aggregates
            summary = {
                'period_minutes': minutes,
                'data_points': len(recent_metrics),
                'cpu_avg': 0,
                'memory_avg': 0,
                'disk_avg': 0,
                'network_in_total': 0,
                'network_out_total': 0
            }
            
            cpu_values = []
            memory_values = []
            disk_values = []
            
            for metrics in recent_metrics:
                if 'cpu' in metrics and 'usage_percent' in metrics['cpu']:
                    cpu_values.append(metrics['cpu']['usage_percent'])
                
                if 'memory' in metrics and 'virtual' in metrics['memory']:
                    memory_values.append(metrics['memory']['virtual']['percent_used'])
                
                if 'disk' in metrics:
                    for disk_name, disk_info in metrics['disk'].items():
                        if isinstance(disk_info, dict) and 'percent_used' in disk_info:
                            disk_values.append(disk_info['percent_used'])
                
                if 'network' in metrics and 'io' in metrics['network']:
                    summary['network_in_total'] += metrics['network']['io'].get('bytes_recv', 0)
                    summary['network_out_total'] += metrics['network']['io'].get('bytes_sent', 0)
            
            if cpu_values:
                summary['cpu_avg'] = sum(cpu_values) / len(cpu_values)
            
            if memory_values:
                summary['memory_avg'] = sum(memory_values) / len(memory_values)
            
            if disk_values:
                summary['disk_avg'] = sum(disk_values) / len(disk_values)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {str(e)}")
            return {}
    
    def start_continuous_collection(self):
        """Start continuous metrics collection"""
        logger.info("Starting continuous metrics collection")
        
        while True:
            try:
                # Collect system metrics
                system_metrics = self.collect_system_metrics()
                if system_metrics:
                    self.store_metrics(system_metrics)
                
                # Collect application metrics
                app_metrics = self.collect_application_metrics()
                if app_metrics:
                    self.store_metrics(app_metrics)
                
                time.sleep(self.collection_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping metrics collection")
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
