import logging
import threading
import time
import psutil
import subprocess
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from ..utils.logger import LogManager
from ..utils.resource import ResourceManager

class MonitorService:
    """监控服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('MonitorService')
        self.log_manager = LogManager(config)
        self.resource_manager = ResourceManager(config)
        self.running = False
        self.monitor_thread = None
        self.callbacks = []
        self.alerts = []
        self.metrics_history = []
        self.max_history = config.get('monitor', {}).get('max_history', 1000)
        self.alert_thresholds = config.get('monitor', {}).get('alert_thresholds', {
            'cpu_percent': 90,
            'memory_percent': 90,
            'disk_percent': 90
        })
        
    def start(self):
        """启动监控服务"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop(self):
        """停止监控服务"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 获取资源使用情况
                usage = self.resource_manager.get_usage()
                
                # 合并指标
                metrics = {
                    'resource_usage': usage,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # 检查告警
                self._check_alerts(metrics)
                
                # 保存历史数据
                self._save_metrics(metrics)
                
                # 记录监控数据
                self.log_manager.log_task_event('monitor', 'metrics', metrics)
                
                # 调用回调函数
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        self.logger.error(f"Error in monitor callback: {e}")
                        
                # 等待下一次监控
                time.sleep(self.config.get('monitor', {}).get('interval', 5))
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)
                
    def _check_alerts(self, metrics: Dict[str, Any]):
        """检查告警
        
        Args:
            metrics: 监控指标
        """
        # 检查CPU使用率
        if metrics['cpu']['percent'] > self.alert_thresholds['cpu_percent']:
            self._add_alert('cpu', f"CPU usage is {metrics['cpu']['percent']}%")
            
        # 检查内存使用率
        if metrics['memory']['percent'] > self.alert_thresholds['memory_percent']:
            self._add_alert('memory', f"Memory usage is {metrics['memory']['percent']}%")
            
        # 检查磁盘使用率
        if metrics['disk']['percent'] > self.alert_thresholds['disk_percent']:
            self._add_alert('disk', f"Disk usage is {metrics['disk']['percent']}%")
            
    def _add_alert(self, alert_type: str, message: str):
        """添加告警
        
        Args:
            alert_type: 告警类型
            message: 告警消息
        """
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.alerts.append(alert)
        self.log_manager.log_task_event('monitor', 'alert', alert)
        
    def _save_metrics(self, metrics: Dict[str, Any]):
        """保存指标
        
        Args:
            metrics: 监控指标
        """
        self.metrics_history.append(metrics)
        
        # 限制历史数据大小
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
            
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
            
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标
        
        Returns:
            Dict[str, Any]: 监控指标
        """
        usage = self.resource_manager.get_usage()
        return {
            'resource_usage': usage
        }
        
    def get_metrics_history(self, duration: timedelta = None) -> List[Dict[str, Any]]:
        """获取历史指标
        
        Args:
            duration: 时间范围
            
        Returns:
            List[Dict[str, Any]]: 历史指标
        """
        if not duration:
            return self.metrics_history
            
        now = datetime.utcnow()
        return [
            m for m in self.metrics_history
            if now - datetime.fromisoformat(m['timestamp']) <= duration
        ]
        
    def get_alerts(self, duration: timedelta = None) -> List[Dict[str, Any]]:
        """获取告警
        
        Args:
            duration: 时间范围
            
        Returns:
            List[Dict[str, Any]]: 告警列表
        """
        if not duration:
            return self.alerts
            
        now = datetime.utcnow()
        return [
            a for a in self.alerts
            if now - datetime.fromisoformat(a['timestamp']) <= duration
        ]
        
    def check_resources(self) -> bool:
        """检查资源是否可用
        
        Returns:
            bool: 是否可用
        """
        return self.resource_manager.check_resources()
        
    def limit_bandwidth(self, process: subprocess.Popen, bandwidth_limit: int):
        """限制带宽
        
        Args:
            process: 进程对象
            bandwidth_limit: 带宽限制（KB/s）
        """
        self.resource_manager.limit_bandwidth(process, bandwidth_limit)
        
    def remove_bandwidth_limit(self):
        """移除带宽限制"""
        self.resource_manager.remove_bandwidth_limit() 