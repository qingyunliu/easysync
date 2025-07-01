import os
import psutil
import logging
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime

class ResourceManager:
    """资源管理类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('ResourceManager')
        self.current_usage = {
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'network': 0
        }

    def check_resources(self) -> bool:
        """检查资源是否可用
        
        Returns:
            bool: 是否可用
        """
        try:
            # 检查CPU使用率
            if self.current_usage['cpu'] > self.config.get('cpu_limit', 80):
                return False
                
            # 检查内存使用率
            if self.current_usage['memory'] > self.config.get('memory_limit', 80):
                return False
                
            # 检查磁盘使用率
            if self.current_usage['disk'] > self.config.get('disk_limit', 80):
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking resources: {e}")
            return False
            
    def get_usage(self) -> Dict[str, Any]:
        """获取资源使用情况
        
        Returns:
            Dict[str, Any]: 资源使用情况
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'network': psutil.net_io_counters().bytes_recv
        }
    
    def limit_bandwidth(self, process: subprocess.Popen, bandwidth_limit: int):
        """限制带宽
        
        Args:
            process: 进程对象
            bandwidth_limit: 带宽限制（KB/s）
        """
        try:
            # 使用tc命令限制带宽
            cmd = [
                'tc', 'qdisc', 'add', 'dev', 'eth0', 'root', 'tbf',
                'rate', f'{bandwidth_limit}kbit',
                'burst', '32kbit',
                'latency', '400ms'
            ]
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            self.logger.error(f"Error limiting bandwidth: {e}")
            raise
            
    def remove_bandwidth_limit(self):
        """移除带宽限制"""
        try:
            cmd = ['tc', 'qdisc', 'del', 'dev', 'eth0', 'root']
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            self.logger.error(f"Error removing bandwidth limit: {e}")
            raise 