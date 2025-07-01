import logging
import threading
import time
import platform
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from .communication import ServerCommunication
from ..services.monitor_service import MonitorService
from ..services.sync_service import SyncService

class ProxyAgent:
    """代理类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('ProxyAgent')
        self.server_comm = ServerCommunication(config)
        self.monitor_service = MonitorService(config)
        self.sync_service = SyncService(config)
        self.running = False
        self.heartbeat_thread = None
        self.health_check_thread = None
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        self.health_check_interval = self.config.get('health_check_interval', 60)
        self._setup_services()
        
    def _setup_services(self):
        """设置服务"""
        # 设置监控服务回调
        self.monitor_service.add_callback(self._on_monitor_update)
        
        # 设置同步服务回调
        self.sync_service.add_callback(self._on_sync_update)
        
    def start(self):
        """启动代理"""
        if self.running:
            return
            
        self.running = True
        self.logger.info("Starting ProxyAgent...")
        
        # 注册节点
        self._register_node()
        
        # 启动监控服务
        self.monitor_service.start()
        self.logger.info("Monitor service started")
        
        # 启动同步服务
        self.sync_service.start()
        self.logger.info("Sync service started")
        
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        self.logger.info("Heartbeat thread started")
        
        # 启动健康检查线程
        self.health_check_thread = threading.Thread(target=self._health_check_loop)
        self.health_check_thread.daemon = True
        self.health_check_thread.start()
        self.logger.info("Health check thread started")
        
    def stop(self):
        """停止代理"""
        if not self.running:
            return
            
        self.running = False
        self.logger.info("Stopping ProxyAgent...")
        
        # 停止服务
        self.monitor_service.stop()
        self.sync_service.stop()
        
        # 等待线程结束
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
            
        self.logger.info("ProxyAgent stopped")
        
    def wait(self):
        """等待代理运行"""
        while self.running:
            time.sleep(1)
            
    def _register_node(self):
        """注册节点"""
        node_info = {
            'hostname': platform.node(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'node_id': str(uuid.uuid4())
        }
        
        node_id = self.server_comm.register_node(node_info)
        if not node_id:
            raise Exception("Failed to register node")
            
        self.config['node_id'] = node_id
        self.logger.info(f"Node registered with ID: {node_id}")
        
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                # 获取系统信息
                system_info = self.monitor_service.get_metrics()
                
                # 发送心跳
                if not self.server_comm.send_heartbeat(system_info):
                    self.logger.warning("Failed to send heartbeat")
                    
                # 获取任务并添加到同步服务
                tasks = self.server_comm.get_tasks()
                if tasks:
                    for task in tasks:
                        self.sync_service.add_task(task)
                        
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                
            # 等待下一次心跳
            time.sleep(self.heartbeat_interval)
            
    def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                # 检查监控服务
                if not self.monitor_service.is_running():
                    self.logger.warning("Monitor service is not running, restarting...")
                    self.monitor_service.stop()
                    self.monitor_service.start()
                    
                # 检查同步服务
                if not self.sync_service.is_running():
                    self.logger.warning("Sync service is not running, restarting...")
                    self.sync_service.stop()
                    self.sync_service.start()
                    
                # 清理旧任务
                self.sync_service.cleanup_old_tasks()
                
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                
            # 等待下一次检查
            time.sleep(self.health_check_interval)
            
    def _on_monitor_update(self, metrics: Dict[str, Any]):
        """处理监控更新
        
        Args:
            metrics: 监控指标
        """
        self.logger.debug(f"Monitor update: {metrics}")
        
    def _on_sync_update(self, status: Dict[str, Any]):
        """处理同步更新
        
        Args:
            status: 同步状态
        """
        self.logger.debug(f"Sync update: {status}")
        
    def is_healthy(self) -> bool:
        """检查代理是否健康
        
        Returns:
            bool: 是否健康
        """
        try:
            # 检查服务是否运行
            if not self.monitor_service.is_running():
                return False
            if not self.sync_service.is_running():
                return False
                
            # 检查线程是否运行
            if not self.heartbeat_thread or not self.heartbeat_thread.is_alive():
                return False
            if not self.health_check_thread or not self.health_check_thread.is_alive():
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking health: {e}")
            return False 