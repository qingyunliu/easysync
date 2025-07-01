import logging
import threading
import queue
import time
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from ..core.storage import StorageManager
from ..core.communication import ServerCommunication
from ..utils.logger import LogManager
from ..utils.resource import ResourceManager
from ..models.task_state import TaskState
from ..core.progress import ProgressMonitor
import uuid

class SyncService:
    """同步服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('SyncService')
        self.storage_manager = StorageManager(config)
        self.log_manager = LogManager(config)
        self.resource_manager = ResourceManager(config)
        self.task_state = TaskState(config.get('state_dir', 'state'))
        self.server_comm = ServerCommunication(config)
        self.progress_monitor = ProgressMonitor(self._on_progress_update)
        self.running = False
        self.sync_thread = None
        self.task_queue = queue.Queue()
        self.max_retries = config.get('sync', {}).get('max_retries', 3)
        self.retry_delay = config.get('sync', {}).get('retry_delay', 5)
        self.max_concurrent = config.get('sync', {}).get('max_concurrent', 1)
        self.active_tasks = 0
        self.task_lock = threading.Lock()
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
        """检查服务是否运行
        
        Returns:
            bool: 是否运行
        """
        return self.running and self.sync_thread and self.sync_thread.is_alive()
        
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加回调函数
        
        Args:
            callback: 回调函数
        """
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """移除回调函数
        
        Args:
            callback: 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    def add_task(self, task: Dict[str, Any]):
        """添加任务
        
        Args:
            task: 任务信息
        """
        try:
            # 检查任务是否已存在
            task_id = task.get('task_id')
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
        """同步循环"""
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
                except queue.Empty:
                    time.sleep(1)
                    continue
                    
                # 执行任务
                with self.task_lock:
                    self.active_tasks += 1
                    
                try:
                    self._execute_task(task)
                finally:
                    with self.task_lock:
                        self.active_tasks -= 1
                        
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                time.sleep(5)
                
    def _execute_task(self, task: Dict[str, Any]):
        """执行同步任务
        
        Args:
            task: 任务信息
        """
        task_id = task['task_id']
        source_config = task['source']
        target_config = task['destination']
        options = task.get('options', {})
        
        # 初始化任务状态
        self.task_state.save_state(task_id, {
            'status': 'running',
            'source': source_config,
            'destination': target_config,
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
        for retry in range(self.max_retries):
            try:
                # 使用StorageManager执行同步
                success = self.storage_manager.sync_data(
                    source_config,
                    target_config,
                    options,
                    self._on_progress_update
                )
                
                if success:
                    self._update_task_status(task_id, 'completed')
                    return
                    
            except Exception as e:
                self.logger.error(f"Error executing task {task_id}: {e}")
                if retry < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                    
            self._update_task_status(task_id, 'failed', str(e))
            
    def _check_storage(self, source_config: Dict[str, Any], target_config: Dict[str, Any]) -> bool:
        """检查存储
        
        Args:
            source_config: 源存储配置
            target_config: 目标存储配置
            
        Returns:
            bool: 是否可用
        """
        try:
            # 检查源存储
            if not self.storage_manager.check_storage(source_config):
                self.logger.error(f"Source storage not available: {source_config}")
                return False
                
            # 检查目标存储
            if not self.storage_manager.check_storage(target_config):
                self.logger.error(f"Destination storage not available: {target_config}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking storage: {e}")
            return False
            
    def _update_task_status(self, task_id: str, status: str, error: str = None):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态
            error: 错误信息
        """
        # 更新本地状态
        self.task_state.save_state(task_id, {
            'status': status,
            'end_time': datetime.utcnow().isoformat(),
            'error': error
        })
        
        # 通知服务器
        self.server_comm.update_task_status(
            task_id,
            {'status': status, 'error': error}
        )
        
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务状态
        """
        try:
            # 优先从本地状态获取
            local_state = self.task_state.load_state(task_id)
            if local_state:
                return local_state
                
            # 如果本地没有，从服务器获取
            return self.server_comm.get_task_status(task_id)
            
        except Exception as e:
            self.logger.error(f"Error getting task status: {e}")
            return None
            
    def _on_progress_update(self, status: Dict[str, Any]):
        """处理进度更新
        
        Args:
            status: 进度状态
        """
        # 更新本地状态
        self.task_state.save_state(status['task_id'], {
            'progress': status['progress'],
            'transferred_files': status['transferred_files'],
            'total_files': status['total_files'],
            'transferred_size': status['transferred_size'],
            'total_size': status['total_size']
        })
        
        # 记录日志
        self.log_manager.log_task_event('sync', 'progress', status)
        
        # 调用回调函数
        for callback in self.callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")
                
    def cleanup_old_tasks(self, max_age_days: int = 7):
        """清理旧任务
        
        Args:
            max_age_days: 最大保留天数
        """
        self.task_state.cleanup_old_states(max_age_days) 