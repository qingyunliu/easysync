import threading
import queue
import time
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from ..core.storage import StorageManager
from ..core.communication import ServerCommunication
from ..core.task_manager import TaskManager
from ..utils.logger import get_log_manager
from ..utils.resource import ResourceManager
from ..models.task_state import TaskState
from ..core.progress import ProgressMonitor
import uuid

class SyncService:
    """同步服务类 - 专注于同步逻辑，任务管理交给 TaskManager"""
    
    def __init__(self, config: Dict[str, Any], server_comm: ServerCommunication = None, task_manager: TaskManager = None):
        self.config = config
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('SyncService')
        
        # 依赖注入
        self.server_comm = server_comm if server_comm else ServerCommunication(config)
        self.task_manager = task_manager  # 任务管理完全交给 TaskManager
        self.storage_manager = StorageManager(config, task_manager)  # 传递 task_manager
        self.resource_manager = ResourceManager(config)
        self.task_state = TaskState(config.get('state_dir', 'state'))
        self.progress_monitor = ProgressMonitor(self._on_progress_update)
        
        # 同步服务状态
        self.running = False
        self.sync_thread = None
        self.task_queue = queue.Queue()
        
        # 同步配置
        self.max_retries = config.get('sync', {}).get('max_retries', 3)
        self.retry_delay = config.get('sync', {}).get('retry_delay', 5)
        self.max_concurrent = config.get('sync', {}).get('max_concurrent', 1)
        self.active_tasks = 0
        self.task_lock = threading.Lock()
        
        # 回调函数
        self.callbacks = []
        
    def start(self):
        """启动同步服务"""
        if self.running:
            return
            
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        
    def stop(self):
        """停止同步服务"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
            
    def is_running(self) -> bool:
        """检查服务是否运行"""
        return self.running and self.sync_thread and self.sync_thread.is_alive()
        
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加回调函数"""
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """移除回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    def cancel_task(self, task_id: str) -> bool:
        """取消任务 - 直接委托给 TaskManager"""
        if self.task_manager:
            return self.task_manager.cancel_task(task_id)
        else:
            self.logger.warning("TaskManager 不可用，无法取消任务")
            return False
            
    def add_task(self, task: Dict[str, Any]):
        """添加任务到队列"""
        try:
            # 检查任务是否已存在
            task_id = task.get('id', task.get('task_id'))
            if not task_id:
                task_id = str(uuid.uuid4())
                task['task_id'] = task_id
                
            # 检查任务状态
            existing_state = self.task_state.load_state(task_id)
            if existing_state and existing_state['status'] in ['completed', 'failed']:
                self.logger.warning(f"Task {task_id} already completed or failed")
                return
                
            # 添加到任务队列
            self.task_queue.put(task)
            self.logger.info(f"Task {task_id} added to queue")
            
        except Exception as e:
            self.logger.error(f"Error adding task: {e}")
            
    def _sync_loop(self):
        """同步循环 - 专注于任务执行逻辑"""
        while self.running:
            try:
                # 检查是否有可用资源
                if not self.resource_manager.check_resources():
                    time.sleep(5)
                    continue
                    
                # 检查并发限制
                with self.task_lock:
                    if self.active_tasks >= self.max_concurrent:
                        time.sleep(1)
                        continue
                        
                    # 获取任务
                    try:
                        task = self.task_queue.get_nowait()
                        self.active_tasks += 1
                    except queue.Empty:
                        time.sleep(1)
                        continue
                
                # 在新线程中执行任务
                task_thread = threading.Thread(
                    target=self._execute_task_with_cleanup,
                    args=(task,),
                    daemon=True
                )
                task_thread.start()
                
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                time.sleep(5)
                
    def _execute_task_with_cleanup(self, task: Dict[str, Any]):
        """执行任务并清理资源"""
        try:
            self._execute_task(task)
        finally:
            with self.task_lock:
                self.active_tasks -= 1
                
    def _execute_task(self, task: Dict[str, Any]):
        """执行任务"""
        task_type = task.get('type', 'sync')
        
        if task_type == 'sync':
            self._execute_sync_task(task)
        elif task_type == 'copy':
            self._execute_copy_task(task)
        elif task_type == 'mount_check':
            self._execute_mount_check_task(task)
        else:
            self.logger.error(f"Unknown task type: {task_type}")
            
    def _execute_sync_task(self, task: Dict[str, Any]):
        """执行同步任务 - 专注于同步逻辑"""
        task_id = task.get('id', task.get('task_id'))
        source_config = task.get('source_storage_config', task.get('source', {}))
        target_config = task.get('target_storage_config', task.get('target', {}))
        options = task.get('options', {})
        
        self.logger.info(f"执行同步任务: {task_id}")
        
        # 初始化任务状态
        self.task_state.save_state(task_id, {
            'status': 'running',
            'source': source_config,
            'target': target_config,
            'source_path': task.get('source_path', ''),
            'target_path': task.get('target_path', ''),
            'options': options,
            'start_time': datetime.utcnow().isoformat(),
            'progress': 0,
            'error': None
        })
        
        # 检查存储
        if not self._check_storage(source_config, target_config):
            self._update_task_status(task_id, 'failed', 'Storage check failed')
            return
            
        # 开始同步
        self.progress_monitor.start()
        
        # 执行同步命令
        last_error = None
        for retry in range(self.max_retries):
            try:
                # 创建带task_id的回调函数
                def progress_callback(status):
                    status['task_id'] = task_id
                    self._on_progress_update(status)
                
                # 获取源端和目标端路径
                source_path = task.get('source_path', '')
                target_path = task.get('target_path', '')
                
                self.logger.info(f"同步路径: {source_path} -> {target_path}")
                
                # 使用StorageManager执行同步
                success = self.storage_manager.sync_data(
                    source_config,
                    target_config,
                    options,
                    progress_callback,
                    source_path=source_path,
                    target_path=target_path,
                    task_id=task_id
                )
                
                if success:
                    self._update_task_status(task_id, 'completed')
                    return
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Error executing sync task {task_id}: {e}")
                if retry < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                    
        # 所有重试都失败了
        self._update_task_status(task_id, 'failed', last_error or 'Unknown error')
    
    def _execute_copy_task(self, task: Dict[str, Any]):
        """执行复制任务"""
        task_id = task.get('id', task.get('task_id'))
        source_config = task.get('source_storage_config', task.get('source', {}))
        target_config = task.get('target_storage_config', task.get('target', {}))
        options = task.get('options', {})
        
        # 初始化任务状态
        self.task_state.save_state(task_id, {
            'status': 'running',
            'source': source_config,
            'target': target_config,
            'options': options,
            'start_time': datetime.utcnow().isoformat(),
            'progress': 0,
            'error': None
        })
        
        # 检查存储
        if not self._check_storage(source_config, target_config):
            self._update_task_status(task_id, 'failed', 'Storage check failed')
            return
            
        # 开始复制
        self.progress_monitor.start()
        
        # 执行复制命令
        last_error = None
        for retry in range(self.max_retries):
            try:
                # 创建带task_id的回调函数
                def progress_callback(status):
                    status['task_id'] = task_id
                    self._on_progress_update(status)
                
                # 使用StorageManager执行复制
                success = self.storage_manager.copy_data(
                    source_config,
                    target_config,
                    options,
                    progress_callback
                )
                
                if success:
                    self._update_task_status(task_id, 'completed')
                    return
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Error executing copy task {task_id}: {e}")
                if retry < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                    
        # 所有重试都失败了
        self._update_task_status(task_id, 'failed', last_error or 'Unknown error')
    
    def _execute_mount_check_task(self, task: Dict[str, Any]):
        """执行挂载检查任务"""
        task_id = task.get('id', task.get('task_id'))
        storage_config = task.get('storage_config', {})
        
        self.logger.info(f"执行挂载检查任务: {task_id}")
        
        try:
            # 执行挂载检查
            mount_result = self.storage_manager.check_mount(storage_config)
            
            # 更新任务状态
            self.server_comm.update_task_status(task_id, {
                'status': 'completed',
                'progress': 100,
                'details': mount_result
            })
            
            self.logger.info(f"Mount check task {task_id} completed")
            
        except Exception as e:
            self.logger.error(f"Error executing mount check task {task_id}: {e}")
            self.server_comm.update_task_status(task_id, {
                'status': 'failed',
                'error': str(e)
            })
            
    def _check_storage(self, source_config: Dict[str, Any], target_config: Dict[str, Any]) -> bool:
        """检查存储连接"""
        try:
            # 检查源存储
            if not self.storage_manager.check_storage(source_config):
                self.logger.error("Source storage check failed")
                return False
                
            # 检查目标存储
            if not self.storage_manager.check_storage(target_config):
                self.logger.error("Target storage check failed")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Storage check failed: {e}")
            return False
            
    def _update_task_status(self, task_id: str, status: str, error: str = None):
        """更新任务状态"""
        try:
            # 更新本地状态
            self.task_state.save_state(task_id, {
                'status': status,
                'error': error,
                'completed_at': datetime.utcnow().isoformat()
            })
            
            # 上报到服务器
            self.server_comm.update_task_status(task_id, {
                'status': status,
                'error': error,
                'completed_at': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error updating task status: {e}")
            
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            return self.task_state.load_state(task_id)
        except Exception as e:
            self.logger.error(f"Error getting task status: {e}")
            return None
            
    def _on_progress_update(self, status: Dict[str, Any]):
        """处理进度更新"""
        try:
            # 调用回调函数
            for callback in self.callbacks:
                try:
                    callback(status)
                except Exception as e:
                    self.logger.error(f"Progress callback error: {e}")
                    
            # 上报进度到服务器
            task_id = status.get('task_id')
            if task_id:
                self.server_comm.update_task_status(task_id, {
                    'status': 'running',
                    'progress': status.get('progress', 0),
                    'details': status
                })
                
        except Exception as e:
            self.logger.error(f"Error in progress update: {e}")
            
    def cleanup_old_tasks(self, max_age_days: int = 7):
        """清理旧任务"""
        try:
            self.task_state.cleanup_old_states(max_age_days)
            self.logger.info(f"Cleaned up tasks older than {max_age_days} days")
        except Exception as e:
            self.logger.error(f"Error cleaning up old tasks: {e}") 