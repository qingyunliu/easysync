import time
import psutil
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MonitorManager:
    def __init__(self, sio, user_id: str, client_id: str, interval: int = 30, metrics: List[str] = None):
        self.sio = sio
        self.user_id = user_id
        self.client_id = client_id
        self.interval = interval
        self.metrics = metrics or ['cpu', 'memory', 'disk', 'network']
        self._running = False
        
    def start(self):
        """启动监控"""
        self._running = True
        while self._running:
            try:
                metrics_data = self.collect_metrics()
                self._send_metrics(metrics_data)
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"采集监控数据失败: {e}")
                time.sleep(5)  # 发生错误时等待5秒后重试
                
    def stop(self):
        """停止监控"""
        self._running = False
        
    def collect_metrics(self) -> Dict[str, Any]:
        """采集系统指标"""
        metrics = {
            'timestamp': datetime.now().timestamp(),  # 使用 Unix 时间戳
            'client_id': self.client_id,
            'user_id': self.user_id
        }
        
        if 'cpu' in self.metrics:
            metrics['cpu'] = {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_avg': list(psutil.getloadavg())
            }
            
        if 'memory' in self.metrics:
            memory = psutil.virtual_memory()
            metrics['memory'] = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free,
                'percent': memory.percent
            }
            
        if 'disk' in self.metrics:
            disk_partitions = psutil.disk_partitions()
            metrics['disk'] = []  # 使用列表存储所有分区数据
            
            for partition in disk_partitions:
                try:
                    # 跳过特殊文件系统
                    if partition.fstype in ('squashfs', 'devtmpfs', 'tmpfs'):
                        continue
                        
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    metrics['disk'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fs_type': partition.fstype,
                        'opts': partition.opts,
                        'total': disk_usage.total,
                        'used': disk_usage.used,
                        'free': disk_usage.free,
                        'percent': disk_usage.percent
                    })
                except (PermissionError, OSError) as e:
                    logger.warning(f"无法获取分区 {partition.mountpoint} 的使用情况: {e}")
                    continue
            
        if 'network' in self.metrics:
            net_io = psutil.net_io_counters()
            metrics['network'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
        return metrics
        
    def _send_metrics(self, metrics_data: Dict[str, Any]):
        """发送监控数据"""
        self.sio.emit('metrics', metrics_data)
        logger.debug(f"发送监控数据: {metrics_data}") 