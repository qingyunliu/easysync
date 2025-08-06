import requests
import time
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta
from ..core.communication import ServerCommunication
from ..utils.logger import get_log_manager
import psutil
import json
import os

class MonitorService:
    """Enhanced monitoring service with alerting capabilities"""
    def __init__(self, config, node_id, token):
        self.config = config
        self._node_id = node_id
        self._token = token
        self.callbacks = []
        self.running = False
        self.server_comm = ServerCommunication(config)
        self.interval = self.config.get('monitor', {}).get('interval', 5)
        self.alert_thresholds = self.config.get('monitor', {}).get('alert_thresholds', {})
        self.alert_cooldown = self.config.get('monitor', {}).get('alert_cooldown', 300)  # 5分钟冷却
        self.last_alerts = {}
        self.metrics_history = []
        self.max_history_size = 100
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('MonitorService')
        self.monitor_thread = None
        
        # 默认告警阈值
        self.default_thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'load_avg_1m': 2.0,
            'network_error_rate': 0.1
        }
        
        # 合并配置的阈值
        self.thresholds = {**self.default_thresholds, **self.alert_thresholds}
        
        # 初始化时更新 ServerCommunication 的认证信息
        self._update_server_comm_auth()
    
    @property
    def node_id(self):
        return self._node_id
    
    @node_id.setter
    def node_id(self, value):
        self._node_id = value
        self._update_server_comm_auth()
    
    @property
    def token(self):
        return self._token
    
    @token.setter
    def token(self, value):
        self._token = value
        self._update_server_comm_auth()
    
    def _update_server_comm_auth(self):
        """更新 ServerCommunication 的认证信息"""
        if self._node_id and self._token:
            self.server_comm.node_id = self._node_id
            self.server_comm.token = self._token
            # 同时更新配置中的认证信息
            if 'node' not in self.config:
                self.config['node'] = {}
            self.config['node']['id'] = self._node_id
            self.config['node']['token'] = self._token
        
    def start(self):
        """启动监控服务"""
        if self.running:
            self.logger.warning("Monitor service is already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info(f"Monitor service started with interval: {self.interval}s")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                metrics = self.collect_metrics()
                self.process_metrics(metrics)
                self.report_metrics(metrics)
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                time.sleep(5)
                
    def stop(self):
        self.running = False

    def collect_metrics(self):
        """收集系统指标"""
        try:
            # 采集CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg()
            
            # 采集内存指标
            memory = psutil.virtual_memory()
            
            # 采集磁盘指标
            disk = psutil.disk_usage('/')
            
            # 采集网络指标
            network = psutil.net_io_counters()
            
            # 采集进程指标
            process_count = len(psutil.pids())
            
            # 采集系统启动时间
            boot_time = psutil.boot_time()
            
            return {
                'node_id': self.node_id,
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg': list(load_avg)
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'free': memory.free,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv,
                    'packets_dropped': getattr(network, 'dropin', 0) + getattr(network, 'dropout', 0)
                },
                'system': {
                    'process_count': process_count,
                    'boot_time': boot_time,
                    'uptime': time.time() - boot_time
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return None
        
    def process_metrics(self, metrics):
        """处理指标数据"""
        if not metrics:
            return
            
        # 存储历史数据
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
            
        # 检查告警
        self.check_alerts(metrics)
        
        # 调用回调函数
        for callback in self.callbacks:
            try:
                callback(metrics)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
                
    def check_alerts(self, metrics):
        """检查告警条件"""
        alerts = []
        current_time = datetime.utcnow()
        
        # CPU告警
        if metrics['cpu']['percent'] > self.thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'level': 'warning',
                'message': f"CPU usage is {metrics['cpu']['percent']:.1f}%",
                'value': metrics['cpu']['percent'],
                'threshold': self.thresholds['cpu_percent']
            })
            
        # 内存告警
        if metrics['memory']['percent'] > self.thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'level': 'warning',
                'message': f"Memory usage is {metrics['memory']['percent']:.1f}%",
                'value': metrics['memory']['percent'],
                'threshold': self.thresholds['memory_percent']
            })
            
        # 磁盘告警
        if metrics['disk']['percent'] > self.thresholds['disk_percent']:
            alerts.append({
                'type': 'disk_high',
                'level': 'critical',
                'message': f"Disk usage is {metrics['disk']['percent']:.1f}%",
                'value': metrics['disk']['percent'],
                'threshold': self.thresholds['disk_percent']
            })
            
        # 负载告警
        if metrics['cpu']['load_avg'][0] > self.thresholds['load_avg_1m']:
            alerts.append({
                'type': 'load_high',
                'level': 'warning',
                'message': f"Load average (1m) is {metrics['cpu']['load_avg'][0]:.2f}",
                'value': metrics['cpu']['load_avg'][0],
                'threshold': self.thresholds['load_avg_1m']
            })
            
        # 发送告警
        for alert in alerts:
            self.send_alert(alert, current_time)
            
    def send_alert(self, alert, current_time):
        """发送告警"""
        alert_key = f"{alert['type']}_{self.node_id}"
        
        # 检查冷却时间
        if alert_key in self.last_alerts:
            time_diff = (current_time - self.last_alerts[alert_key]).total_seconds()
            if time_diff < self.alert_cooldown:
                return
                
        # 记录告警时间
        self.last_alerts[alert_key] = current_time
        
        # 构造告警数据
        alert_data = {
            'node_id': self.node_id,
            'alert_type': alert['type'],
            'level': alert['level'],
            'message': alert['message'],
            'value': alert['value'],
            'threshold': alert['threshold'],
            'timestamp': current_time.isoformat()
        }
        
        # 发送到服务器
        try:
            self.server_comm.send_alert(alert_data)
            self.logger.warning(f"Alert sent: {alert['message']}")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
            
    def report_metrics(self, metrics):
        """上报指标数据"""
        if not metrics:
            return False
            
        try:
            success = self.server_comm.report_metrics(metrics)
            if success:
                self.logger.debug(f"Metrics reported successfully")
            else:
                self.logger.warning(f"Failed to report metrics")
            return success
        except Exception as e:
            self.logger.error(f"Error reporting metrics: {e}")
            return False
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """获取当前指标"""
        return self.collect_metrics()
        
    def get_metrics_history(self, limit: int = 10) -> list:
        """获取历史指标"""
        return self.metrics_history[-limit:]
        
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        if not self.metrics_history:
            return {'status': 'unknown', 'message': 'No metrics available'}
            
        latest_metrics = self.metrics_history[-1]
        
        # 检查各项指标
        issues = []
        
        if latest_metrics['cpu']['percent'] > self.thresholds['cpu_percent']:
            issues.append(f"High CPU usage: {latest_metrics['cpu']['percent']:.1f}%")
            
        if latest_metrics['memory']['percent'] > self.thresholds['memory_percent']:
            issues.append(f"High memory usage: {latest_metrics['memory']['percent']:.1f}%")
            
        if latest_metrics['disk']['percent'] > self.thresholds['disk_percent']:
            issues.append(f"High disk usage: {latest_metrics['disk']['percent']:.1f}%")
            
        if latest_metrics['cpu']['load_avg'][0] > self.thresholds['load_avg_1m']:
            issues.append(f"High load average: {latest_metrics['cpu']['load_avg'][0]:.2f}")
            
        if issues:
            return {
                'status': 'unhealthy',
                'message': '; '.join(issues),
                'issues': issues
            }
        else:
            return {
                'status': 'healthy',
                'message': 'All metrics are within normal ranges'
            }
            
    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """更新告警阈值"""
        self.thresholds.update(new_thresholds)
        self.logger.info(f"Updated alert thresholds: {new_thresholds}")
        
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加监控回调
        
        Args:
            callback: 回调函数
        """
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """移除监控回调
        
        Args:
            callback: 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)