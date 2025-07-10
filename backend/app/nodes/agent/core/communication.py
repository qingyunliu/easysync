import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

class ServerCommunication:
    """服务器通信类（适配新版Agent API）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('ServerCommunication')
        self.server_url = self._get_server_url()
        self.session = requests.Session()
        self.node_id = None
        self.token = self.config.get('agent_token')
        
    def _get_server_url(self) -> str:
        """获取服务器URL"""
        server_config = self.config.get('server', {})
        host = server_config.get('host', 'localhost')
        port = server_config.get('port', 5000)
        return f"http://{host}:{port}/api/agent/v1/nodes"
        
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
            self.node_id = data.get('node_id')
            self.token = data.get('token')
            self.config['agent_token'] = self.token
            return self.node_id
            
        except Exception as e:
            self.logger.error(f"Error registering node: {e}")
            return None
            
    def send_heartbeat(self, heartbeat_info: Dict[str, Any]) -> bool:
        """发送心跳
        
        Args:
            system_info: 系统信息
            
        Returns:
            bool: 是否成功
        """
        if not self.node_id or not self.token:
            self.logger.error("Node not registered or token missing")
            return False
            
        try:
            url = f"{self.server_url}/{self.node_id}/heartbeat"
            data = {'heartbeat': heartbeat_info}
            response = self.session.post(url, json=data, headers=self._auth_headers())
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
            response = self.session.put(url, json=status, headers=self._auth_headers())
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
            url = f"{self.server_url}/nodes/{self.node_id}/tasks/{task_id}/status"
            response = self.session.get(url)
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
            url = f"{self.server_url}/nodes/{self.node_id}/storage/mount"
            data = {
                'node_id': self.node_id,
                'storage_config': storage_config
            }
            
            response = self.session.post(url, json=data)
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
            url = f"{self.server_url}/nodes/{self.node_id}/storage/unmount"
            data = {
                'node_id': self.node_id,
                'mount_point': mount_point
            }
            
            response = self.session.post(url, json=data)
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
            response = self.session.post(url, json={'metrics': metrics}, headers=self._auth_headers())
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
            response = self.session.post(url, json=error, headers=self._auth_headers())
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error reporting error: {e}")
            return False 