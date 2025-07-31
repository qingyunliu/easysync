import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend import db
from backend.app.models import Task, Node, TaskStatus
from .service import TaskService

logger = logging.getLogger(__name__)

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.task_service = TaskService()
        self.running = False
        self.thread = None
        self.app = None  # Flask应用实例
        self.max_tasks_per_node = 5  # 每个节点最大并发任务数
        self.scheduler_interval = 10  # 调度间隔（秒）
        self.node_health_check_interval = 60  # 节点健康检查间隔（秒）
        
    def start(self):
        """启动调度器"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Task scheduler started")
        
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Task scheduler stopped")
        
    def _run_scheduler(self):
        """运行调度器"""
        last_health_check = datetime.utcnow()
        
        while self.running:
            try:
                # 分发待分配任务
                self._dispatch_pending_tasks()
                
                # 检查超时任务
                self._check_timeout_tasks()
                
                # 定期健康检查
                now = datetime.utcnow()
                if (now - last_health_check).seconds >= self.node_health_check_interval:
                    self._check_node_health()
                    last_health_check = now
                    
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                
            time.sleep(self.scheduler_interval)
            
    def _dispatch_pending_tasks(self):
        """分发待分配任务"""
        try:
            with self.app.app_context():
                # 获取所有待分配任务
                pending_tasks = self.task_service.get_pending_tasks()
                
                if not pending_tasks:
                    return
                    
                # 获取所有在线节点
                online_nodes = Node.query.filter_by(status='online').all()
                
                if not online_nodes:
                    logger.warning("No online nodes available for task dispatch")
                    return
                    
                # 为每个任务分配最合适的节点
                for task in pending_tasks:
                    try:
                        best_node = self._find_best_node(task, online_nodes)
                        if best_node:
                            self.task_service.assign_task(task.id, best_node.id)
                            logger.info(f"Task {task.id} assigned to node {best_node.id}")
                        else:
                            logger.warning(f"No available node for task {task.id}")
                    except Exception as e:
                        logger.error(f"Failed to assign task {task.id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in dispatch_pending_tasks: {e}")
            
    def _find_best_node(self, task: Task, nodes: List[Node]) -> Optional[Node]:
        """找到最合适的节点"""
        best_node = None
        min_running_tasks = float('inf')
        
        for node in nodes:
            # 检查节点是否健康
            if not self._is_node_healthy(node):
                continue
                
            # 检查节点是否有agent运行
            if node.agent_status != 'running':
                continue
                
            # 获取节点当前运行的任务数
            running_tasks = Task.query.filter_by(
                node_id=node.id, 
                status='running'
            ).count()
            
            # 检查是否超过最大并发数
            if running_tasks >= self.max_tasks_per_node:
                continue
                
            # 选择负载最轻的节点
            if running_tasks < min_running_tasks:
                min_running_tasks = running_tasks
                best_node = node
                
        return best_node
        
    def _is_node_healthy(self, node: Node) -> bool:
        """检查节点是否健康"""
        if not node.last_heartbeat:
            return False
            
        # 检查心跳时间
        time_since_heartbeat = datetime.utcnow() - node.last_heartbeat
        return time_since_heartbeat.seconds < 120  # 2分钟内有心跳
        
    def _check_timeout_tasks(self):
        """检查超时任务"""
        try:
            with self.app.app_context():
                timeout_threshold = datetime.utcnow() - timedelta(seconds=self.task_service.task_timeout)
                
                # 查找超时的运行中任务
                timeout_tasks = Task.query.filter(
                    Task.status == 'running',
                    Task.started_at < timeout_threshold
                ).all()
                
                for task in timeout_tasks:
                    try:
                        # 将超时任务标记为失败
                        task.status = 'failed'
                        task.error = 'Task timeout'
                        task.completed_at = datetime.utcnow()
                        db.session.commit()
                        
                        logger.warning(f"Task {task.id} marked as failed due to timeout")
                        
                    except Exception as e:
                        logger.error(f"Failed to handle timeout task {task.id}: {e}")
                        db.session.rollback()
                        
        except Exception as e:
            logger.error(f"Error in check_timeout_tasks: {e}")
            
    def _check_node_health(self):
        """检查节点健康状态"""
        try:
            with self.app.app_context():
                # 获取所有节点
                nodes = Node.query.all()
                
                for node in nodes:
                    was_online = node.status == 'online'
                    is_healthy = self._is_node_healthy(node)
                    
                    if was_online and not is_healthy:
                        # 节点从在线变为离线
                        node.status = 'offline'
                        db.session.commit()
                        
                        # 处理该节点上的运行中任务
                        self._handle_offline_node_tasks(node.id)
                        
                        logger.warning(f"Node {node.id} went offline")
                        
        except Exception as e:
            logger.error(f"Error in check_node_health: {e}")
            
    def _handle_offline_node_tasks(self, node_id: str):
        """处理离线节点上的任务"""
        try:
            with self.app.app_context():
                # 获取节点上所有运行中的任务
                running_tasks = Task.query.filter_by(
                    node_id=node_id, 
                    status='running'
                ).all()
                
                for task in running_tasks:
                    try:
                        # 将任务重新标记为待分配
                        task.status = 'pending'
                        task.node_id = None
                        task.assigned_at = None
                        task.started_at = None
                        task.error = 'Node went offline'
                        
                        db.session.commit()
                        
                        logger.info(f"Task {task.id} reassigned due to node offline")
                        
                    except Exception as e:
                        logger.error(f"Failed to reassign task {task.id}: {e}")
                        db.session.rollback()
                        
        except Exception as e:
            logger.error(f"Error in handle_offline_node_tasks: {e}")
            
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            'running': self.running,
            'pending_tasks': Task.query.filter_by(status='pending').count(),
            'running_tasks': Task.query.filter_by(status='running').count(),
            'online_nodes': Node.query.filter_by(status='online').count(),
            'scheduler_interval': self.scheduler_interval,
            'max_tasks_per_node': self.max_tasks_per_node
        }
        
    def manually_dispatch_task(self, task_id: str, node_id: Optional[str] = None) -> bool:
        """手动分发任务"""
        try:
            task = self.task_service.get_task(task_id)
            
            if task.status != 'pending':
                return False
                
            if node_id:
                # 分配给指定节点
                node = Node.query.get(node_id)
                if not node or not self._is_node_healthy(node):
                    return False
                    
                self.task_service.assign_task(task_id, node_id)
                return True
            else:
                # 自动分配
                online_nodes = Node.query.filter_by(status='online').all()
                best_node = self._find_best_node(task, online_nodes)
                
                if best_node:
                    self.task_service.assign_task(task_id, best_node.id)
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to manually dispatch task {task_id}: {e}")
            
        return False

# 全局调度器实例
scheduler = TaskScheduler() 