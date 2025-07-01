import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend import db
from backend.app.models import Node, Task
from .errors import NodeNotFoundError, NodeUnhealthyError, NodeOperationError

logger = logging.getLogger(__name__)

class NodeService:
    """节点服务类"""
    
    def __init__(self):
        self.heartbeat_timeout = 300  # 5分钟超时
        self.max_tasks_per_node = 10  # 每个节点最大任务数
        
    def get_node(self, node_id: str) -> Node:
        """获取节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            Node: 节点对象
            
        Raises:
            NodeNotFoundError: 节点不存在
        """
        node = Node.query.get(node_id)
        if not node:
            raise NodeNotFoundError(f"Node not found: {node_id}")
        return node
        
    def check_node_health(self, node: Node) -> bool:
        """检查节点健康状态
        
        Args:
            node: 节点对象
            
        Returns:
            bool: 是否健康
        """
        # 检查心跳
        if not node.last_heartbeat:
            return False
            
        # 检查心跳超时
        if datetime.utcnow() - node.last_heartbeat > timedelta(seconds=self.heartbeat_timeout):
            return False
            
        # 检查系统资源
        if node.system_info:
            cpu_percent = node.system_info.get('cpu_percent', 0)
            memory_percent = node.system_info.get('memory_percent', 0)
            if cpu_percent > 90 or memory_percent > 90:
                return False
                
        return True
        
    def update_node_heartbeat(self, node_id: str, system_info: Dict[str, Any]) -> None:
        """更新节点心跳
        
        Args:
            node_id: 节点ID
            system_info: 系统信息
            
        Raises:
            NodeNotFoundError: 节点不存在
        """
        node = self.get_node(node_id)
        node.last_heartbeat = datetime.utcnow()
        node.system_info = system_info
        db.session.commit()
        
    def get_node_tasks(self, node_id: str) -> List[Dict[str, Any]]:
        """获取节点任务
        
        Args:
            node_id: 节点ID
            
        Returns:
            List[Dict[str, Any]]: 任务列表
            
        Raises:
            NodeNotFoundError: 节点不存在
            NodeUnhealthyError: 节点不健康
        """
        node = self.get_node(node_id)
        
        # 检查节点健康状态
        if not self.check_node_health(node):
            raise NodeUnhealthyError(f"Node is unhealthy: {node_id}")
            
        # 获取节点任务
        tasks = Task.query.filter_by(node_id=node_id, status='pending').all()
        
        # 检查任务数量限制
        if len(tasks) >= self.max_tasks_per_node:
            return []
            
        return [task.to_dict() for task in tasks]
        
    def update_task_status(self, node_id: str, task_id: str, status: Dict[str, Any]) -> None:
        """更新任务状态
        
        Args:
            node_id: 节点ID
            task_id: 任务ID
            status: 任务状态
            
        Raises:
            NodeNotFoundError: 节点不存在
            NodeOperationError: 操作错误
        """
        node = self.get_node(node_id)
        task = Task.query.get(task_id)
        
        if not task:
            raise NodeOperationError(f"Task not found: {task_id}")
            
        if task.node_id != node_id:
            raise NodeOperationError(f"Task does not belong to node: {node_id}")
            
        # 更新任务状态
        task.status = status.get('status')
        task.progress = status.get('progress', 0)
        task.error = status.get('error')
        task.updated_at = datetime.utcnow()
        
        # 记录任务日志
        logger.info(f"Task status updated: {task_id}, status: {status}")
        
        db.session.commit()
        
    def mount_storage(self, node_id: str, storage_config: Dict[str, Any]) -> None:
        """挂载存储
        
        Args:
            node_id: 节点ID
            storage_config: 存储配置
            
        Raises:
            NodeNotFoundError: 节点不存在
            NodeOperationError: 操作错误
        """
        node = self.get_node(node_id)
        
        # 验证存储配置
        if not self._validate_storage_config(storage_config):
            raise NodeOperationError("Invalid storage configuration")
            
        # 更新节点配置
        if 'storage' not in node.config:
            node.config['storage'] = {}
            
        node.config['storage'][storage_config['mount_point']] = storage_config
        db.session.commit()
        
        logger.info(f"Storage mounted: {node_id}, config: {storage_config}")
        
    def unmount_storage(self, node_id: str, mount_point: str) -> None:
        """卸载存储
        
        Args:
            node_id: 节点ID
            mount_point: 挂载点
            
        Raises:
            NodeNotFoundError: 节点不存在
            NodeOperationError: 操作错误
        """
        node = self.get_node(node_id)
        
        # 检查挂载点是否存在
        if 'storage' not in node.config or mount_point not in node.config['storage']:
            raise NodeOperationError(f"Mount point not found: {mount_point}")
            
        # 移除存储配置
        del node.config['storage'][mount_point]
        db.session.commit()
        
        logger.info(f"Storage unmounted: {node_id}, mount_point: {mount_point}")
        
    def _validate_storage_config(self, config: Dict[str, Any]) -> bool:
        """验证存储配置
        
        Args:
            config: 存储配置
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['type', 'mount_point']
        return all(field in config for field in required_fields) 

    def get_node_details(self, node_id: str) -> Dict[str, Any]:
        """获取节点信息
        
        Args:
            node_id: 节点ID
            
        Returns:
            Dict[str, Any]: 节点信息
        """
        node = self.get_node(node_id)
        

