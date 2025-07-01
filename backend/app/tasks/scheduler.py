import threading
import time
from typing import Optional
from sqlalchemy.orm import Session
from app.tasks.assigner import TaskAssigner
from app.tasks.service import TaskService
from app.tasks.models import Task, TaskStatus

class TaskScheduler:
    def __init__(self, db: Session):
        self.db = db
        self.task_service = TaskService(db)
        self.task_assigner = TaskAssigner(db)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """启动调度器"""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """停止调度器"""
        if not self._thread or not self._thread.is_alive():
            return

        self._stop_event.set()
        self._thread.join()

    def _run(self):
        """调度器主循环"""
        while not self._stop_event.is_set():
            try:
                # 分配任务
                self.task_assigner.assign_tasks()
                
                # 检查超时任务
                self._check_timeout_tasks()
                
                # 等待下一次调度
                time.sleep(10)  # 每10秒调度一次
            except Exception as e:
                print(f"Task scheduler error: {str(e)}")
                time.sleep(5)  # 发生错误时等待5秒后继续

    def _check_timeout_tasks(self):
        """检查超时任务"""
        # 获取所有运行中的任务
        running_tasks = self.db.query(Task)\
            .filter(Task.status == TaskStatus.RUNNING)\
            .all()

        for task in running_tasks:
            # 检查任务是否超时
            if self._is_task_timeout(task):
                # 更新任务状态为失败
                self.task_service.update_task_status(
                    task.task_id,
                    TaskStatus.FAILED,
                    error="Task timeout"
                )

    def _is_task_timeout(self, task: Task) -> bool:
        """检查任务是否超时"""
        if not task.started_at:
            return False

        # 获取任务超时时间（秒）
        timeout = task.options.get('timeout', 3600)  # 默认1小时

        # 计算任务运行时间
        running_time = (time.time() - task.started_at.timestamp())
        return running_time > timeout 