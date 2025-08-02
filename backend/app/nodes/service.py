import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend import db
from backend.app.models import Node, Task
from backend.app.notifications.services import NotificationService
from .errors import NodeNotFoundError, NodeUnhealthyError, NodeOperationError
import threading
import uuid
from backend.app.utils.ssh_utils import SSHClient

INSTALL_TASKS = {}

logger = logging.getLogger(__name__)

class NodeService:
    """节点服务类"""
    
    def __init__(self):
        self.heartbeat_timeout = 300  # 5分钟超时
        self.max_tasks_per_node = 10  # 每个节点最大任务数
        self.notification_service = NotificationService()
        
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
        previous_status = node.agent_status
        current_time = datetime.utcnow()
        
        # 更新心跳信息
        node.last_heartbeat = current_time
        node.system_info = system_info
        
        # 检查节点状态变化
        is_healthy = self.check_node_health(node)
        new_status = 'online' if is_healthy else 'offline'
        
        # 更新节点状态
        if node.agent_status != new_status:
            node.agent_status = new_status
            
            # 发送状态变更通知
            self._send_node_status_notification(node, previous_status, new_status)
        
        # 检查资源警告
        self._check_resource_warnings(node, system_info)
        
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
        
        return {
            'id': node.id,
            'name': node.name,
            'ipaddress': node.ipaddress,
            'status': node.status,
            'agent_status': node.agent_status,
            'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
            'system_info': node.system_info,
            'config': node.config,
            'created_at': node.created_at.isoformat() if node.created_at else None
        }
    
    # =============== 通知相关方法 ===============
    
    def _send_node_status_notification(self, node: Node, previous_status: str, new_status: str) -> None:
        """发送节点状态变更通知"""
        try:
            # 获取节点IP地址
            node_ip = node.ipaddress
            
            # 节点上线
            if new_status == 'online' and previous_status != 'online':
                # 通知所有管理员
                self.notification_service.notify_all_admins(
                    notification_type='node_online',
                    title=f'节点上线: {node.name}',
                    content=f'节点 {node.name} 已成功上线。\nIP地址: {node_ip}',
                    level='success'
                )
            
            # 节点离线
            elif new_status == 'offline' and previous_status != 'offline':
                reason = "心跳超时"
                if node.last_heartbeat:
                    time_diff = datetime.utcnow() - node.last_heartbeat
                    if time_diff.total_seconds() > self.heartbeat_timeout:
                        reason = f"心跳超时 ({int(time_diff.total_seconds())}秒)"
                
                # 通知所有管理员
                self.notification_service.notify_all_admins(
                    notification_type='node_offline',
                    title=f'节点离线: {node.name}',
                    content=f'节点 {node.name} 已离线。\n原因: {reason}\nIP地址: {node_ip}',
                    level='warning'
                )
                
        except Exception as e:
            logger.error(f"发送节点状态通知失败: {str(e)}")
    
    def _check_resource_warnings(self, node: Node, system_info: Dict[str, Any]) -> None:
        """检查资源使用情况并发送警告通知"""
        try:
            # CPU使用率警告
            cpu_percent = system_info.get('cpu_percent', 0)
            if cpu_percent > 85:
                self.notification_service.notify_all_admins(
                    notification_type='node_resource_warning',
                    title=f'节点资源警告: {node.name}',
                    content=f'节点 {node.name} 的CPU使用率已达到 {cpu_percent:.1f}%，请及时处理。\nIP地址: {node.ipaddress}',
                    level='warning'
                )
            
            # 内存使用率警告
            memory_percent = system_info.get('memory_percent', 0)
            if memory_percent > 85:
                self.notification_service.notify_all_admins(
                    notification_type='node_resource_warning',
                    title=f'节点资源警告: {node.name}',
                    content=f'节点 {node.name} 的内存使用率已达到 {memory_percent:.1f}%，请及时处理。\nIP地址: {node.ipaddress}',
                    level='warning'
                )
            
            # 磁盘使用率警告
            disk_info = system_info.get('disk_usage', {})
            for disk_path, usage in disk_info.items():
                if isinstance(usage, dict) and usage.get('percent', 0) > 85:
                    self.notification_service.notify_all_admins(
                        notification_type='node_resource_warning',
                        title=f'节点磁盘警告: {node.name}',
                        content=f'节点 {node.name} 的磁盘 {disk_path} 使用率已达到 {usage["percent"]:.1f}%，请及时处理。\nIP地址: {node.ipaddress}',
                        level='warning'
                    )
                    
        except Exception as e:
            logger.error(f"检查节点资源警告失败: {str(e)}")
    
    def notify_node_error(self, node_id: str, error_message: str) -> None:
        """通知节点错误"""
        try:
            node = self.get_node(node_id)
            
            # 通知所有管理员
            self.notification_service.notify_all_admins(
                notification_type='node_error',
                title=f'节点错误: {node.name}',
                content=f'节点 {node.name} 发生错误。\n错误信息: {error_message}\nIP地址: {node.ipaddress}',
                level='error'
            )
            
        except Exception as e:
            logger.error(f"发送节点错误通知失败: {str(e)}")
    
    def check_node_timeouts(self) -> None:
        """检查节点心跳超时并发送通知"""
        try:
            # 获取所有在线节点
            online_nodes = Node.query.filter_by(agent_status='online').all()
            current_time = datetime.utcnow()
            
            for node in online_nodes:
                if node.last_heartbeat:
                    time_diff = current_time - node.last_heartbeat
                    
                    # 如果心跳超时，更新状态并发送通知
                    if time_diff.total_seconds() > self.heartbeat_timeout:
                        previous_status = node.agent_status
                        node.agent_status = 'offline'
                        db.session.commit()
                        
                        # 发送心跳超时通知
                        self.notification_service.notify_all_admins(
                            notification_type='node_heartbeat_timeout',
                            title=f'节点心跳超时: {node.name}',
                            content=f'节点 {node.name} 心跳超时，已自动标记为离线。\n'
                                   f'最后心跳时间: {node.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")}\n'
                                   f'超时时长: {int(time_diff.total_seconds())} 秒\n'
                                   f'IP地址: {node.ipaddress}',
                            level='warning'
                        )
                        
                        logger.warning(f"Node {node.id} ({node.name}) marked as offline due to heartbeat timeout")
                        
        except Exception as e:
            logger.error(f"检查节点超时失败: {str(e)}")
    
    def notify_node_created(self, node: Node, user_id: str) -> None:
        """通知节点创建成功"""
        try:
            self.notification_service.create_notification(
                user_id=user_id,
                type='node_created',
                title=f'节点创建成功: {node.name}',
                content=f'节点 {node.name} 已成功创建并配置。\nIP地址: {node.ipaddress}',
                level='success'
            )
            
        except Exception as e:
            logger.error(f"发送节点创建通知失败: {str(e)}")
    
    def notify_node_deleted(self, node_name: str, node_ip: str, user_id: str) -> None:
        """通知节点删除"""
        try:
            self.notification_service.create_notification(
                user_id=user_id,
                type='node_deleted',
                title=f'节点已删除: {node_name}',
                content=f'节点 {node_name} 已被删除，相关配置已清理。\nIP地址: {node_ip}',
                level='info'
            )
            
        except Exception as e:
            logger.error(f"发送节点删除通知失败: {str(e)}")