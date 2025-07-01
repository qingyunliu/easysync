import os
import yaml
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_path: str, reload_interval: int = 60):
        self.config_path = config_path
        self.reload_interval = reload_interval
        self._config = {}
        self._last_modified = 0
        self._lock = threading.Lock()
        self._callbacks = []
        self._running = False
        self._reload_thread = None
        
    def start(self):
        """启动配置管理器"""
        if self._running:
            return
            
        self._running = True
        self._reload_thread = threading.Thread(target=self._reload_loop, daemon=True)
        self._reload_thread.start()
        
    def stop(self):
        """停止配置管理器"""
        self._running = False
        if self._reload_thread:
            self._reload_thread.join()
            
    def _reload_loop(self):
        """配置重载循环"""
        while self._running:
            try:
                self._check_and_reload()
            except Exception as e:
                logger.error(f"配置重载失败: {e}")
            time.sleep(self.reload_interval)
            
    def _check_and_reload(self):
        """检查并重载配置"""
        try:
            current_modified = os.path.getmtime(self.config_path)
            if current_modified > self._last_modified:
                self.reload()
        except Exception as e:
            logger.error(f"检查配置文件修改时间失败: {e}")
            
    def reload(self):
        """重载配置"""
        try:
            with open(self.config_path, 'r') as f:
                new_config = yaml.safe_load(f)
                
            with self._lock:
                old_config = self._config.copy()
                self._config = new_config
                self._last_modified = os.path.getmtime(self.config_path)
                
            # 通知配置变更
            self._notify_config_changed(old_config, new_config)
            
            logger.info("配置重载成功")
            return True
            
        except Exception as e:
            logger.error(f"配置重载失败: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        with self._lock:
            return self._config.get(key, default)
            
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        with self._lock:
            return self._config.copy()
            
    def register_callback(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]):
        """注册配置变更回调"""
        self._callbacks.append(callback)
        
    def _notify_config_changed(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """通知配置变更"""
        for callback in self._callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                logger.error(f"配置变更回调执行失败: {e}")
                
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问配置"""
        return self.get(key)
        
    def __contains__(self, key: str) -> bool:
        """检查配置项是否存在"""
        with self._lock:
            return key in self._config 