from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models import Task, TaskStatus
from backend.app.models import Node, NodeStatus
from backend.app.tasks.service import TaskService

class TaskAssigner:
    def __init__(self, db: Session):
        self.db = db
        self.task_service = TaskService(db)

    def assign_tasks(self) -> List[Task]:
        """分配待处理的任务"""
        # 获取所有在线节点
        online_nodes = self.db.query(Node)\
            .filter(Node.status == NodeStatus.ONLINE)\
            .all()
        
        if not online_nodes:
            return []

        # 获取待分配的任务
        pending_tasks = self.task_service.get_pending_tasks()
        if not pending_tasks:
            return []

        assigned_tasks = []
        for task in pending_tasks:
            # 选择最适合的节点
            node = self._select_best_node(online_nodes, task)
            if node:
                # 分配任务
                assigned_task = self.task_service.assign_task(task.task_id, node.node_id)
                if assigned_task:
                    assigned_tasks.append(assigned_task)

        return assigned_tasks

    def _select_best_node(self, nodes: List[Node], task: Task) -> Optional[Node]:
        """选择最适合的节点"""
        if not nodes:
            return None

        # 根据节点负载和任务优先级选择节点
        best_node = None
        min_load = float('inf')

        for node in nodes:
            # 计算节点负载
            load = self._calculate_node_load(node)
            
            # 如果节点负载小于当前最小负载，更新最佳节点
            if load < min_load:
                min_load = load
                best_node = node

        return best_node

    def _calculate_node_load(self, node: Node) -> float:
        """计算节点负载"""
        # 获取节点正在运行的任务数
        running_tasks = self.db.query(Task)\
            .filter(Task.assigned_node == node.node_id)\
            .filter(Task.status == TaskStatus.RUNNING)\
            .count()

        # 获取节点已分配但未开始的任务数
        assigned_tasks = self.db.query(Task)\
            .filter(Task.assigned_node == node.node_id)\
            .filter(Task.status == TaskStatus.ASSIGNED)\
            .count()

        # 计算总负载
        total_load = running_tasks + (assigned_tasks * 0.5)  # 已分配但未开始的任务权重较低

        # 考虑节点性能指标
        if node.metrics:
            cpu_percent = node.metrics.get('cpu_percent', 0)
            memory_percent = node.metrics.get('memory_percent', 0)
            # 将性能指标纳入负载计算
            total_load += (cpu_percent + memory_percent) / 200  # 归一化到0-1范围

        return total_load 