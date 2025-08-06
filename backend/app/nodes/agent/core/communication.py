import os
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
from ..utils.logger import get_log_manager

class ServerCommunication:
    """服务器通信类（适配新版Agent API）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('ServerCommunication')
        self.server_url = self._get_server_url()
        self.session = requests.Session()
        self.user_id = None
        self.node_id = None
        self.token = None
        self._get_node_config()
        
    def _get_server_url(self) -> str:
        """获取服务器URL"""
        server_config = self.config.get('server', {})
        host = server_config.get('host', 'localhost')
        port = server_config.get('port', 5000)
        return f"http://{host}:{port}/api/agent"
    
    def _get_node_config(self) -> str:
        """获取Node认证信息"""
        node_config = self.config.get('node', {})
        self.user_id = node_config.get('user', '')
        self.node_id = node_config.get('id', '')
        self.token = node_config.get('token', '')
        
    def _auth_headers(self):
        if not self.token:
            return {}
        return {'Authorization': f'Bearer {self.token}'}
        
    def register_node(self, node_info: Dict[str, Any]) -> Optional[str]:
        """注册节点
        
        Args:
            node_info: 节点信息
            
        Returns:
            Optional[str]: 节点ID
        """
        try:
            url = f"{self.server_url}/register"
            response = self.session.post(url, json=node_info)
            response.raise_for_status()
            data = response.json().get('data', {})
            self.node_id = data.get('id')
            self.user_id = data.get('user_id')
            self.token = data.get('token')
            if 'node' not in self.config:
                self.config['node'] = {}
            self.config['node']['token'] = self.token
            return self.node_id
            
        except Exception as e:
            self.logger.error(f"Error registering node: {e}")
            return None
            
    def send_heartbeat(self, heartbeat_info: Dict[str, Any]) -> bool:
        """发送心跳
        
        Args:
            heartbeat_info: 心跳信息
            
        Returns:
            bool: 是否成功
        """
        if not self.node_id or not self.token:
            self.logger.error("Node not registered or token missing")
            return False
            
        try:
            url = f"{self.server_url}/{self.node_id}/heartbeat"
            self.logger.debug(f"Sending heartbeat to {url}, data: {heartbeat_info}")
            response = self.session.post(url, json=heartbeat_info, headers=self._auth_headers())
            self.logger.debug(f"Heartbeat response: {response.json()}")
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
            return False
            
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取待执行的任务
        
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        if not self.node_id or not self.token:
            self.logger.error("Node not registered or token missing")
            return []
            
        try:
            url = f"{self.server_url}/{self.node_id}/tasks"
            response = self.session.get(url, headers=self._auth_headers())
            self.logger.debug(f"Getting tasks from {url}, received tasks data: {response.json()}")
            response.raise_for_status()
            
            return response.json().get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting tasks: {e}")
            return []
            
    def update_task_status(self, task_id: str, status: Dict[str, Any]) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 任务状态
            
        Returns:
            bool: 是否成功
        """
        if not self.node_id or not self.token:
            self.logger.error("Node not registered or token missing")
            return False
            
        try:
            url = f"{self.server_url}/{self.node_id}/tasks/{task_id}/status"
            self.logger.debug(f"Updating task status to {url}, data: {status}")
            response = self.session.put(url, json=status, headers=self._auth_headers())
            self.logger.debug(f"Task status update response: {response.json()}")
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating task status: {e}")
            return False
            
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务状态
        """
        if not self.node_id:
            self.logger.error("Node not registered")
            return None
            
        try:
            url = f"{self.server_url}/{self.node_id}/tasks/{task_id}"
            self.logger.debug(f"Getting task status from {url}")
            response = self.session.get(url)
            self.logger.debug(f"Task status response: {response.json()}")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Error getting task status: {e}")
            return None
            
    def mount_storage(self, storage_config: Dict[str, Any]) -> bool:
        """挂载存储
        
        Args:
            storage_config: 存储配置
            
        Returns:
            bool: 是否成功
        """
        if not self.node_id:
            self.logger.error("Node not registered")
            return False
            
        try:
            url = f"{self.server_url}/{self.node_id}/storage/mount"
            data = {
                'node_id': self.node_id,
                'storage_config': storage_config
            }
            self.logger.debug(f"Mounting storage to {url}, data: {data}")
            response = self.session.post(url, json=data)
            self.logger.debug(f"Mount storage response: {response.json()}")
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error mounting storage: {e}")
            return False
            
    def unmount_storage(self, mount_point: str) -> bool:
        """卸载存储
        
        Args:
            mount_point: 挂载点
            
        Returns:
            bool: 是否成功
        """
        if not self.node_id:
            self.logger.error("Node not registered")
            return False
            
        try:
            url = f"{self.server_url}/{self.node_id}/storage/unmount"
            data = {
                'node_id': self.node_id,
                'mount_point': mount_point
            }
            self.logger.debug(f"Unmounting storage to {url}, data: {data}")
            response = self.session.post(url, json=data)
            self.logger.debug(f"Unmount storage response: {response.json()}")
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unmounting storage: {e}")
            return False

    def report_metrics(self, metrics: Dict[str, Any]) -> bool:
        if not self.node_id or not self.token:
            self.logger.error("Node not registered or token missing")
            return False
        try:
            url = f"{self.server_url}/{self.node_id}/metrics"
            self.logger.debug(f"Reporting metrics to {url}, data: {metrics}")
            response = self.session.post(url, json={'metrics': metrics}, headers=self._auth_headers())
            self.logger.debug(f"Metrics report response: {response.json()}")
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error reporting metrics: {e}")
            return False

    def report_error(self, error: Dict[str, Any]) -> bool:
        if not self.node_id or not self.token:
            self.logger.error("Node not registered or token missing")
            return False
        try:
            url = f"{self.server_url}/{self.node_id}/errors"
            self.logger.debug(f"Reporting error to {url}, data: {error}")
            response = self.session.post(url, json=error, headers=self._auth_headers())
            self.logger.debug(f"Error report response: {response.json()}")
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error reporting error: {e}")
            return False

    def get_realtime_commands(self) -> List[Dict[str, Any]]:
        """获取待执行的实时命令
        
        Returns:
            List[Dict[str, Any]]: 实时命令列表
        """
        if not self.node_id or not self.token:
            return []
        
        try:
            url = f"{self.server_url}/{self.node_id}/commands"
            response = self.session.get(url, headers=self._auth_headers())
            self.logger.debug(f"Realtime commands response: {response.json()}")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            self.logger.error(f"Error getting realtime commands: {e}")
            return []
    
    def update_command_status(self, command_id: str, status: Dict[str, Any]) -> bool:
        """更新实时命令状态
        
        Args:
            command_id: 命令ID
            status: 状态信息
            
        Returns:
            bool: 是否成功
        """
        if not self.node_id or not self.token:
            self.logger.error("Node not registered or token missing")
            return False
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                url = f"{self.server_url}/{self.node_id}/commands/{command_id}/status"
                self.logger.debug(f"Updating command status to {url}, data: {status}, attempt: {attempt + 1}")
                response = self.session.put(url, json=status, headers=self._auth_headers(), timeout=10)
                self.logger.debug(f"Command status update response: {response.json()}")
                response.raise_for_status()
                return True
            except Exception as e:
                self.logger.error(f"Error updating command status (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    self.logger.error(f"Failed to update command status after {max_retries} attempts")
                    return False
        
        return False 