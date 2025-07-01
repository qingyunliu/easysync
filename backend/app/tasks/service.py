import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend import db
from backend.app.models import Task, TaskLog, TaskStatus, TaskPriority
from backend.app.models import Node, NodeStatus
from .errors import TaskNotFoundError, TaskOperationError, TaskValidationError, TaskStateError

logger = logging.getLogger(__name__)

class TaskService:
    """任务服务类"""
    
    def __init__(self):
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 300  # 重试延迟（秒）
        self.task_timeout = 3600  # 任务超时时间（秒）
        
    def create_task(self, task_data: Dict[str, Any]) -> Task:
        """创建任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskValidationError: 任务数据验证失败
        """
        # 验证任务数据
        self._validate_task_data(task_data)
        
        # 创建任务
        task = Task(
            name=task_data.get('name'),
            type=task_data['type'],
            source=task_data['source'],
            target=task_data['target'],
            options=task_data.get('options', {}),
            status='pending',
            priority=task_data.get('priority', 0),
            user_id=task_data.get('user_id')
        )
        
        db.session.add(task)
        db.session.commit()
        
        logger.info(f"Task created: {task.id}")
        return task
        
    def get_task(self, task_id: str) -> Task:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
        """
        task = Task.query.get(task_id)
        if not task:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return task
        
    def update_task_status(self, task_id: str, status: Dict[str, Any]) -> Task:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态信息
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskStateError: 状态更新失败
        """
        task = self.get_task(task_id)
        
        # 验证状态更新
        if not self._validate_status_update(task, status):
            raise TaskStateError(f"Invalid status update: {status}")
            
        # 更新状态
        task.status = status.get('status')
        task.progress = status.get('progress', 0)
        task.error = status.get('error')
        task.updated_at = datetime.utcnow()
        
        # 处理任务完成
        if task.status in ['completed', 'failed']:
            task.completed_at = datetime.utcnow()
            
        db.session.commit()
        
        logger.info(f"Task status updated: {task_id}, status: {status}")
        return task
        
    def get_node_tasks(self, node_id: str) -> List[Task]:
        """获取节点任务
        
        Args:
            node_id: 节点ID
            
        Returns:
            List[Task]: 任务列表
        """
        return Task.query.filter_by(node_id=node_id, status='pending').all()
        
    def get_pending_tasks(self) -> List[Task]:
        """获取待分配任务
        
        Returns:
            List[Task]: 任务列表
        """
        return Task.query.filter_by(status='pending').order_by(Task.priority.desc(), Task.created_at.asc()).all()
        
    def assign_task(self, task_id: str, node_id: str) -> Task:
        """分配任务给节点
        
        Args:
            task_id: 任务ID
            node_id: 节点ID
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskOperationError: 操作失败
        """
        task = self.get_task(task_id)
        node = Node.query.get(node_id)
        
        if not node:
            raise TaskOperationError(f"Node not found: {node_id}")
            
        if task.status != 'pending':
            raise TaskOperationError(f"Task is not pending: {task_id}")
            
        # 分配任务
        task.node_id = node_id
        task.status = 'assigned'
        task.assigned_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Task assigned: {task_id} to node: {node_id}")
        return task
        
    def retry_task(self, task_id: str) -> Task:
        """重试任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskOperationError: 操作失败
        """
        task = self.get_task(task_id)
        
        if task.status != 'failed':
            raise TaskOperationError(f"Task is not failed: {task_id}")
            
        if task.retry_count >= self.max_retries:
            raise TaskOperationError(f"Max retries exceeded: {task_id}")
            
        # 重试任务
        task.status = 'pending'
        task.retry_count += 1
        task.error = None
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Task retried: {task_id}, retry count: {task.retry_count}")
        return task
        
    def cancel_task(self, task_id: str) -> Task:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskOperationError: 操作失败
        """
        task = self.get_task(task_id)
        
        if task.status in ['completed', 'failed', 'cancelled']:
            raise TaskOperationError(f"Task cannot be cancelled: {task_id}")
            
        # 取消任务
        task.status = 'cancelled'
        task.updated_at = datetime.utcnow()
        task.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Task cancelled: {task_id}")
        return task
        
    def _validate_task_data(self, data: Dict[str, Any]) -> None:
        """验证任务数据
        
        Args:
            data: 任务数据
            
        Raises:
            TaskValidationError: 验证失败
        """
        required_fields = ['type', 'source', 'target']
        if not all(field in data for field in required_fields):
            raise TaskValidationError("Missing required fields")
            
    def _validate_status_update(self, task: Task, status: Dict[str, Any]) -> bool:
        """验证状态更新
        
        Args:
            task: 任务对象
            status: 状态信息
            
        Returns:
            bool: 是否有效
        """
        new_status = status.get('status')
        if not new_status:
            return False
            
        # 检查状态转换是否有效
        valid_transitions = {
            'pending': ['assigned', 'cancelled'],
            'assigned': ['running', 'cancelled'],
            'running': ['completed', 'failed', 'cancelled'],
            'failed': ['pending', 'cancelled'],
            'completed': [],
            'cancelled': []
        }
        
        return new_status in valid_transitions.get(task.status, [])

    def get_task_logs(self, task_id: str) -> List[TaskLog]:
        """获取任务日志"""
        return self.db.query(TaskLog)\
            .filter(TaskLog.task_id == task_id)\
            .order_by(TaskLog.created_at.asc())\
            .all() 