import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend import db
from backend.app.models import Task, TaskLog, TaskStatus, TaskPriority
from backend.app.models import Node, NodeStatus
from backend.app.notifications.services import NotificationService
from .errors import TaskNotFoundError, TaskOperationError, TaskValidationError, TaskStateError

logger = logging.getLogger(__name__)

class TaskService:
    """任务服务类"""
    
    def __init__(self):
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 300  # 重试延迟（秒）
        self.task_timeout = 3600  # 任务超时时间（秒）
        self.notification_service = NotificationService()
        
    def create_task(self, task_data: Dict[str, Any]) -> Task:
        """创建任务，支持新的业务逻辑结构"""
        # 验证任务数据
        self._validate_task_data(task_data)
        
        task_type = task_data.get('type')
        
        # 构建任务对象，支持新的字段结构
        task = Task(
            name=task_data.get('name'),
            description=task_data.get('description'),
            type=task_type,
            priority=task_data.get('priority', 2),
            status='pending',
            user_id=task_data.get('user_id'),
            node_id=task_data.get('node_id') if task_data.get('node_id') else None,
            # 新的业务逻辑字段
            source_type=task_data.get('source_type'),
            source_client_id=task_data.get('source_client_id') if task_data.get('source_type') == 'client' and task_data.get('source_client_id') else None,
            source_storage_id=task_data.get('source_storage_id') if task_data.get('source_type') == 'storage' and task_data.get('source_storage_id') else None,
            source_path=task_data.get('source_path'),
            target_storage_id=task_data.get('target_storage_id'),
            target_path=task_data.get('target_path'),
            # 兼容旧版本字段
            source=task_data.get('source', {}),
            target=task_data.get('target', {}),
            options=task_data.get('options', {}),
        )
        
        db.session.add(task)
        db.session.commit()
        
        # 记录任务创建日志
        self._add_task_log(task.id, 'created', f"Task '{task.name}' created with type '{task_type}'", {
            'task_type': task_type,
            'priority': task.priority,
            'source_type': task.source_type,
            'source_client_id': task.source_client_id,
            'source_storage_id': task.source_storage_id,
            'source_path': task.source_path,
            'target_storage_id': task.target_storage_id,
            'target_path': task.target_path,
            'options': task.options
        })
        
        logger.info(f"Task created: {task.id} with source_type: {task.source_type}")
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
        """更新任务状态，支持 details 字段存储 agent 回传的检测结果"""
        task = self.get_task(task_id)
        previous_status = task.status
        
        # 验证状态更新
        if not self._validate_status_update(task, status):
            raise TaskStateError(f"Invalid status update: {status}")
        
        # 更新状态
        task.status = status.get('status')
        task.progress = status.get('progress', 0)
        task.error = status.get('error')
        task.updated_at = datetime.utcnow()
        
        # 支持 details 字段
        if 'details' in status:
            task.details = status['details']
        
        # 处理任务完成
        if task.status in ['completed', 'failed']:
            task.completed_at = datetime.utcnow()
        elif task.status == 'running' and previous_status != 'running':
            task.started_at = datetime.utcnow()
        
        # 发送状态变更通知
        self._send_task_notification(task, previous_status)
        
        db.session.commit()
        
        # 记录状态变化日志
        self._add_task_log(task.id, task.status, f"Task status changed from '{previous_status}' to '{task.status}'", {
            'previous_status': previous_status,
            'new_status': task.status,
            'progress': task.progress,
            'error': task.error,
            'details': task.details
        })
        
        logger.info(f"Task status updated: {task_id}, status: {status}")
        return task
        
    def get_node_tasks(self, node_id: str) -> List[Task]:
        """获取节点任务
        
        Args:
            node_id: 节点ID
            
        Returns:
            List[Task]: 任务列表
        """
        return Task.query.filter_by(node_id=node_id, status='assigned').all()
        
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
        
        if task.status != 'failed' and task.status != 'cancelled':
            raise TaskOperationError(f"Task is not failed or cancelled: {task_id}")
            
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
        
    def start_task(self, task_id: str, node_id: str = None) -> Task:
        """启动任务
        
        Args:
            task_id: 任务ID
            node_id: 节点ID（可选，如果不指定则自动分配）
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskOperationError: 操作失败
        """
        task = self.get_task(task_id)
        
        if task.status not in ['pending', 'failed']:
            raise TaskOperationError(f"Task cannot be started: {task_id}, current status: {task.status}")
        
        # 如果指定了节点，分配给该节点
        if node_id:
            # 检查节点是否在线
            node = Node.query.get(node_id)
            if not node or node.status != 'online':
                raise TaskOperationError(f"Node is not available: {node_id}")
                
            task.node_id = node_id
        elif not task.node_id:
            # 自动分配节点
            available_node = self._find_available_node()
            if not available_node:
                raise TaskOperationError("No available nodes to execute the task")
            task.node_id = available_node.id
        
        # 更新任务状态
        task.status = 'assigned'
        task.updated_at = datetime.utcnow()
        task.started_at = datetime.utcnow()
        
        db.session.commit()
        
        # 记录启动日志
        self._add_task_log(task.id, 'assigned', f"Task '{task.name}' assigned to node {task.node_id}", {
            'node_id': task.node_id,
            'started_at': task.started_at.isoformat()
        })
        
        logger.info(f"Task started: {task_id}, assigned to node: {task.node_id}")
        return task
    
    def pause_task(self, task_id: str) -> Task:
        """暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskOperationError: 操作失败
        """
        task = self.get_task(task_id)
        
        if task.status != 'running':
            raise TaskOperationError(f"Task cannot be paused: {task_id}, current status: {task.status}")
        
        # 更新任务状态为暂停请求
        task.status = 'pause_requested'
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 记录暂停日志
        self._add_task_log(task.id, 'pause_requested', f"Task '{task.name}' pause requested", {
            'pause_requested_at': task.updated_at.isoformat()
        })
        
        logger.info(f"Task pause requested: {task_id}")
        return task
    
    def resume_task(self, task_id: str) -> Task:
        """恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 任务对象
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskOperationError: 操作失败
        """
        task = self.get_task(task_id)
        
        if task.status != 'paused':
            raise TaskOperationError(f"Task cannot be resumed: {task_id}, current status: {task.status}")
        
        # 更新任务状态为恢复请求
        task.status = 'resume_requested'
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 记录恢复日志
        self._add_task_log(task.id, 'resume_requested', f"Task '{task.name}' resume requested", {
            'resume_requested_at': task.updated_at.isoformat()
        })
        
        logger.info(f"Task resume requested: {task_id}")
        return task
    
    def delete_task(self, task_id: str, force: bool = False) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            force: 是否强制删除（删除运行中的任务）
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskOperationError: 操作失败
        """
        task = self.get_task(task_id)
        
        if not force and task.status in ['running', 'assigned']:
            raise TaskOperationError(f"Cannot delete running task: {task_id}. Use force=True to force delete.")
        
        # 如果任务正在运行，先取消
        if task.status in ['running', 'assigned']:
            task.status = 'cancel_requested'
            db.session.commit()
            
            # 记录取消日志
            self._add_task_log(task.id, 'cancel_requested', f"Task '{task.name}' cancel requested before deletion", {
                'cancel_requested_at': datetime.utcnow().isoformat(),
                'reason': 'Task deletion'
            })
        
        # 删除相关日志
        TaskLog.query.filter_by(task_id=task_id).delete()
        
        # 删除任务
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"Task deleted: {task_id}")
        return True
    
    def create_connection_test_task(self, storage_config: Dict[str, Any], user_id: int) -> Task:
        """创建连接测试任务
        
        Args:
            storage_config: 存储配置
            user_id: 用户ID
            
        Returns:
            Task: 任务对象
        """
        task_data = {
            'name': f"连接测试 - {storage_config.get('name', 'Unknown')}",
            'description': f"测试存储连接: {storage_config.get('type', 'Unknown')}",
            'type': 'test-connection',
            'priority': 1,  # 高优先级
            'user_id': user_id,
            'source_type': 'storage',
            'options': {
                'storage_config': storage_config,
                'test_type': 'connection'
            }
        }
        
        task = self.create_task(task_data)
        logger.info(f"Connection test task created: {task.id}")
        return task
    
    def create_mount_test_task(self, mount_point: str, storage_config: Dict[str, Any], user_id: int) -> Task:
        """创建挂载测试任务
        
        Args:
            mount_point: 挂载点
            storage_config: 存储配置
            user_id: 用户ID
            
        Returns:
            Task: 任务对象
        """
        task_data = {
            'name': f"挂载测试 - {mount_point}",
            'description': f"测试挂载点: {mount_point}",
            'type': 'mount-check',
            'priority': 1,  # 高优先级
            'user_id': user_id,
            'source_type': 'storage',
            'options': {
                'mount_point': mount_point,
                'storage_config': storage_config,
                'test_type': 'mount'
            }
        }
        
        task = self.create_task(task_data)
        logger.info(f"Mount test task created: {task.id}")
        return task
    
    def get_task_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """获取任务统计信息
        
        Args:
            user_id: 用户ID（可选，如果不指定则获取全部）
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        query = Task.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        tasks = query.all()
        
        stats = {
            'total': len(tasks),
            'pending': len([t for t in tasks if t.status == 'pending']),
            'assigned': len([t for t in tasks if t.status == 'assigned']),
            'running': len([t for t in tasks if t.status == 'running']),
            'completed': len([t for t in tasks if t.status == 'completed']),
            'failed': len([t for t in tasks if t.status == 'failed']),
            'cancelled': len([t for t in tasks if t.status == 'cancelled']),
            'paused': len([t for t in tasks if t.status == 'paused']),
            'by_type': {},
            'by_priority': {}
        }
        
        # 按类型统计
        for task in tasks:
            task_type = task.type or 'unknown'
            stats['by_type'][task_type] = stats['by_type'].get(task_type, 0) + 1
        
        # 按优先级统计
        for task in tasks:
            priority = task.priority or 0
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
        
        return stats
    
    # =============== 通知相关方法 ===============
    
    def _send_task_notification(self, task: Task, previous_status: str) -> None:
        """发送任务状态变更通知"""
        try:
            current_status = task.status
            
            # 任务开始执行
            if current_status == 'running' and previous_status != 'running':
                self.notification_service.notify_task_started(
                    user_id=task.user_id,
                    task_name=task.name
                )
            
            # 任务暂停
            elif current_status == 'paused' and previous_status != 'paused':
                reason = task.error or "用户手动暂停"
                self.notification_service.notify_task_paused(
                    user_id=task.user_id,
                    task_name=task.name,
                    reason=reason
                )
            
            # 任务恢复
            elif current_status == 'running' and previous_status == 'paused':
                self.notification_service.notify_task_resumed(
                    user_id=task.user_id,
                    task_name=task.name
                )
            
            # 任务完成
            elif current_status == 'completed' and previous_status != 'completed':
                # 获取处理统计信息
                files_processed = getattr(task, 'files_processed', 0)
                bytes_processed = getattr(task, 'bytes_processed', 0)
                
                self.notification_service.notify_task_completed(
                    user_id=task.user_id,
                    task_name=task.name,
                    files_processed=files_processed,
                    bytes_processed=bytes_processed
                )
            
            # 任务失败
            elif current_status == 'failed' and previous_status != 'failed':
                error_message = task.error or "未知错误"
                self.notification_service.notify_task_failed(
                    user_id=task.user_id,
                    task_name=task.name,
                    error=error_message
                )
            
            # 任务取消
            elif current_status == 'cancelled' and previous_status != 'cancelled':
                reason = task.error or "用户手动取消"
                self.notification_service.notify_task_cancelled(
                    user_id=task.user_id,
                    task_name=task.name,
                    reason=reason
                )
            
        except Exception as e:
            logger.error(f"发送任务通知失败: {str(e)}")
    
    def retry_failed_task(self, task_id: str, user_id: str) -> Task:
        """重试失败的任务"""
        task = self.get_task(task_id)
        
        # 验证任务状态
        if task.status != 'failed':
            raise TaskStateError(f"只能重试失败的任务，当前状态: {task.status}")
        
        if task.user_id != user_id:
            raise TaskOperationError("无权限操作此任务")
        
        # 增加重试计数
        retry_count = getattr(task, 'retry_count', 0) + 1
        task.retry_count = retry_count
        
        # 检查重试次数限制
        if retry_count > self.max_retries:
            raise TaskOperationError(f"已达到最大重试次数 ({self.max_retries})")
        
        # 重置任务状态
        task.status = 'pending'
        task.error = None
        task.progress = 0
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 发送重试通知
        try:
            self.notification_service.notify_task_retry(
                user_id=task.user_id,
                task_name=task.name,
                retry_count=retry_count,
                max_retries=self.max_retries
            )
        except Exception as e:
            logger.error(f"发送任务重试通知失败: {str(e)}")
        
        # 记录重试日志
        self._add_task_log(
            task.id, 
            'retrying', 
            f"Task retry attempt {retry_count}/{self.max_retries}",
            {'retry_count': retry_count, 'max_retries': self.max_retries}
        )
        
        logger.info(f"Task {task_id} marked for retry ({retry_count}/{self.max_retries})")
        return task
    
    def _find_available_node(self) -> Optional[Node]:
        """查找可用节点
        
        Returns:
            Optional[Node]: 可用节点
        """
        # 查找在线且负载不高的节点
        available_nodes = Node.query.filter_by(status='online').all()
        
        if not available_nodes:
            return None
        
        # 简单的负载均衡：选择任务数最少的节点
        node_task_counts = {}
        for node in available_nodes:
            running_tasks = Task.query.filter_by(
                node_id=node.id, 
                status='running'
            ).count()
            node_task_counts[node.id] = running_tasks
        
        # 选择任务数最少的节点
        best_node_id = min(node_task_counts, key=node_task_counts.get)
        return Node.query.get(best_node_id)

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
            raise TaskOperationError(f"Task cannot be cancelled: {task_id}, current status: {task.status}")
        
        # 如果任务正在运行，设置为取消请求状态，让agent处理
        if task.status in ['running', 'assigned']:
            task.status = 'cancel_requested'
            task.updated_at = datetime.utcnow()
            
            # 记录取消请求日志
            self._add_task_log(task.id, 'cancel_requested', f"Task '{task.name}' cancel requested", {
                'cancel_requested_at': task.updated_at.isoformat(),
                'reason': 'User requested cancellation'
            })
            
            db.session.commit()
            logger.info(f"Task cancel requested: {task_id}")
            
        else:
            # 对于未启动的任务，直接取消
            task.status = 'cancelled'
            task.updated_at = datetime.utcnow()
            task.completed_at = datetime.utcnow()
            
            # 记录取消日志
            self._add_task_log(task.id, 'cancelled', f"Task '{task.name}' was cancelled", {
                'cancelled_at': task.completed_at.isoformat(),
                'reason': 'User cancelled'
            })
            
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
        # 基本字段验证
        required_fields = ['name', 'type', 'source_type']
        for field in required_fields:
            if not data.get(field):
                raise TaskValidationError(f"Missing required field: {field}")
        
        # 验证源端类型
        source_type = data.get('source_type')
        if source_type not in ['client', 'storage']:
            raise TaskValidationError("source_type must be 'client' or 'storage'")
        
        # 根据源端类型验证相应字段
        if source_type == 'client':
            if not data.get('source_client_id'):
                raise TaskValidationError("source_client_id is required when source_type is 'client'")
        elif source_type == 'storage':
            if not data.get('source_storage_id'):
                raise TaskValidationError("source_storage_id is required when source_type is 'storage'")
        
        # 验证路径字段
        if not data.get('source_path'):
            raise TaskValidationError("source_path is required")
        
        # 验证目标端字段
        if not data.get('target_storage_id'):
            raise TaskValidationError("target_storage_id is required")
        
        if not data.get('target_path'):
            raise TaskValidationError("target_path is required")
            
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
        return TaskLog.query\
            .filter(TaskLog.task_id == task_id)\
            .order_by(TaskLog.created_at.asc())\
            .all()
    
    def _add_task_log(self, task_id: str, status: str, message: str, details: Dict[str, Any] = None) -> TaskLog:
        """添加任务日志
        
        Args:
            task_id: 任务ID
            status: 任务状态
            message: 日志消息
            details: 详细信息
            
        Returns:
            TaskLog: 日志对象
        """
        task = self.get_task(task_id)
        
        # 对于进度日志，使用 upsert 模式，只保留最新的一条
        if '同步进度' in message:
            # 查找是否已存在进度日志（获取最新的）
            existing_log = TaskLog.query.filter(
                TaskLog.task_id == task_id,
                TaskLog.message.like('%同步进度%')
            ).order_by(TaskLog.created_at.desc()).first()
            
            if existing_log:
                # 更新现有记录
                existing_log.message = message
                existing_log.details = details or {}
                existing_log.updated_at = datetime.utcnow()
                db.session.commit()
                return existing_log
        
        # 对于其他类型的日志，正常插入
        log = TaskLog(
            task_id=task_id,
            user_id=task.user_id,
            status=status,
            message=message,
            details=details or {}
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def add_task_step_log(self, task_id: str, step_name: str, step_status: str, 
                         step_message: str, step_details: Dict[str, Any] = None) -> TaskLog:
        """添加任务步骤日志
        
        Args:
            task_id: 任务ID
            step_name: 步骤名称
            step_status: 步骤状态
            step_message: 步骤消息
            step_details: 步骤详情
            
        Returns:
            TaskLog: 日志对象
        """
        return self._add_task_log(task_id, f"step_{step_status}", f"Step '{step_name}': {step_message}", {
            'step_name': step_name,
            'step_status': step_status,
            'step_details': step_details or {}
        })
    
    def add_task_progress_log(self, task_id: str, progress: int, current_step: str, 
                            total_steps: int, step_details: Dict[str, Any] = None) -> TaskLog:
        """添加任务进度日志
        
        Args:
            task_id: 任务ID
            progress: 进度百分比
            current_step: 当前步骤
            total_steps: 总步骤数
            step_details: 步骤详情
            
        Returns:
            TaskLog: 日志对象
        """
        return self._add_task_log(task_id, 'progress', f"Progress: {progress}% - {current_step}", {
            'progress': progress,
            'current_step': current_step,
            'total_steps': total_steps,
            'step_details': step_details or {}
        })
    
    def add_task_error_log(self, task_id: str, error_type: str, error_message: str, 
                          error_details: Dict[str, Any] = None) -> TaskLog:
        """添加任务错误日志
        
        Args:
            task_id: 任务ID
            error_type: 错误类型
            error_message: 错误消息
            error_details: 错误详情
            
        Returns:
            TaskLog: 日志对象
        """
        return self._add_task_log(task_id, 'error', f"Error [{error_type}]: {error_message}", {
            'error_type': error_type,
            'error_message': error_message,
            'error_details': error_details or {}
        })
    
    def get_task_execution_summary(self, task_id: str) -> Dict[str, Any]:
        """获取任务执行摘要
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 执行摘要
        """
        task = self.get_task(task_id)
        logs = self.get_task_logs(task_id)
        
        # 统计各状态的日志数量
        status_counts = {}
        error_logs = []
        progress_logs = []
        step_logs = []
        
        for log in logs:
            status = log.status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
            
            if status == 'error':
                error_logs.append(log)
            elif '同步进度' in log.message:
                progress_logs.append(log)
            elif status.startswith('step_'):
                step_logs.append(log)
        
        # 计算执行时间
        execution_time = None
        if task.started_at and task.completed_at:
            execution_time = (task.completed_at - task.started_at).total_seconds()
        elif task.started_at:
            execution_time = (datetime.utcnow() - task.started_at).total_seconds()
        
        return {
            'task_id': task_id,
            'task_name': task.name,
            'task_type': task.type,
            'status': task.status,
            'progress': task.progress,
            'execution_time': execution_time,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'log_summary': {
                'total_logs': len(logs),
                'status_counts': status_counts,
                'error_count': len(error_logs),
                'progress_count': len(progress_logs),
                'step_count': len(step_logs)
            },
            'latest_logs': [log.to_dict() for log in logs[-5:]]  # 最近5条日志
        } 

    def cleanup_old_progress_logs(self, task_id: str = None, days: int = 7):
        """清理过期的进度日志
        
        Args:
            task_id: 任务ID，如果为None则清理所有任务
            days: 保留天数，默认7天
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 构建查询条件
            query = TaskLog.query.filter(
                TaskLog.message.like('%同步进度%'),
                TaskLog.created_at < cutoff_date
            )
            
            # 如果指定了任务ID，则只清理该任务的日志
            if task_id:
                query = query.filter(TaskLog.task_id == task_id)
            
            # 删除过期的进度日志
            deleted_count = query.delete()
            
            db.session.commit()
            logger.info(f"清理了 {deleted_count} 条过期的进度日志")
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"清理进度日志失败: {e}")
            return 0
    
    def cleanup_duplicate_progress_logs(self, task_id: str):
        """清理重复的进度日志，只保留指定任务的最新一条"""
        try:
            # 获取该任务的所有进度日志，按时间倒序
            progress_logs = TaskLog.query.filter(
                TaskLog.task_id == task_id,
                TaskLog.message.like('%同步进度%')
            ).order_by(TaskLog.created_at.desc()).all()
            
            deleted_count = 0
            # 保留最新的一条，删除其他的
            if len(progress_logs) > 1:
                for log in progress_logs[1:]:
                    db.session.delete(log)
                    deleted_count += 1
            
            db.session.commit()
            logger.info(f"任务 {task_id} 清理了 {deleted_count} 条重复的进度日志")
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"清理重复进度日志失败: {e}")
            return 0
    
    def cleanup_all_duplicate_progress_logs(self):
        """清理所有任务的重复进度日志，只保留每个任务的最新一条"""
        try:
            # 获取所有有进度日志的任务
            tasks_with_progress = db.session.query(TaskLog.task_id).filter(
                TaskLog.message.like('%同步进度%')
            ).distinct().all()
            
            total_deleted = 0
            for (task_id,) in tasks_with_progress:
                # 获取该任务的所有进度日志，按时间倒序
                progress_logs = TaskLog.query.filter(
                    TaskLog.task_id == task_id,
                    TaskLog.message.like('%同步进度%')
                ).order_by(TaskLog.created_at.desc()).all()
                
                # 保留最新的一条，删除其他的
                if len(progress_logs) > 1:
                    for log in progress_logs[1:]:
                        db.session.delete(log)
                        total_deleted += 1
            
            db.session.commit()
            logger.info(f"全局清理了 {total_deleted} 条重复的进度日志")
            return total_deleted
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"全局清理重复进度日志失败: {e}")
            return 0 