import requests
import time
from typing import Dict, Any, Callable
from datetime import datetime
from ..core.communication import ServerCommunication
import psutil

class MonitorService:
    """极简监控服务：只采集并HTTP上报，不存历史，不做本地判断"""
    def __init__(self, config, node_id, token):
        self.config = config
        self.node_id = node_id
        self.token = token
        self.callbacks = []
        self.running = False
        self.server_comm = ServerCommunication(config)
        self.interval = self.config.get('monitor', {}).get('interval', 5)
        
    def start(self):
        self.running = True
        while self.running:
            try:
                metrics = self.collect_metrics()
                self.report_metrics(metrics)
                time.sleep(self.interval)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
                
    def stop(self):
        self.running = False

    def collect_metrics(self):
        # 采集cpu、memory、disk、network
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'load_avg': list(psutil.getloadavg())
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
                'packets_recv': network.packets_recv
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    def report_metrics(self, metrics):
        if self.server_comm.report_metrics(metrics):
            self.logger.info(f"Report metrics Success, metrics: {metrics}")
    
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