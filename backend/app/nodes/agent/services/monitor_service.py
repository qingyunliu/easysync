import requests
import time
from datetime import datetime
import psutil

class MonitorService:
    """极简监控服务：只采集并HTTP上报，不存历史，不做本地判断"""
    def __init__(self, config, node_id, token):
        self.config = config
        self.node_id = node_id
        self.token = token
        self.running = False
        self.server_url = self.config['server']['url'] if 'server' in self.config and 'url' in self.config['server'] else self.config.get('server_url')
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
        url = f"{self.server_url}/api/agent/v1/nodes/{self.node_id}/metrics"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            requests.post(url, json={'metrics': metrics}, headers=headers, timeout=5)
        except Exception as e:
            print(f"上报监控数据失败: {e}") 