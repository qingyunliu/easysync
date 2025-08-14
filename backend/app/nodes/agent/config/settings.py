import os
import json
from typing import Dict, Any
from ..utils.logger import get_log_manager

class Settings:
    """配置类"""
    
    def __init__(self, config_path: str = None):
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('Settings')
        self.config_path = config_path or os.getenv('AGENT_CONFIG', 'config.json')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            'server': {
                'host': 'localhost',
                'port': 5001,
                'api_version': 'v1'
            },
            'node': {
                'id': '',
                'user': '',
                'token': ''
            },
            'heartbeat_interval': 30,
            'command': {
                'interval': 3,
                'max_concurrent': 3
            },
            'task': {
                'max_concurrent': 3
            },
            'monitor': {
                'interval': 5,
                'max_history': 1000,
                'alert_thresholds': {
                    'cpu_percent': 90,
                    'memory_percent': 90,
                    'disk_percent': 90
                }
            },
            'sync': {
                'max_retries': 3,
                'retry_delay': 5,
                'max_concurrent': 3
            },
            'state_dir': 'state',
            'log_level': 'INFO'
        }
        
    def get_config(self) -> Dict[str, Any]:
        """获取配置
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        return self.config
        
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置
        
        Args:
            new_config: 新配置
        """
        self.config.update(new_config)
        self.save_config() 