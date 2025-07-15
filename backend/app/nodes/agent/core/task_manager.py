#!/usr/bin/env python3
"""
任务管理器 - 处理任务取消、重试、状态管理等高级功能
"""

import logging
import subprocess
import threading
import time
import signal
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class TaskProcess:
    """任务进程信息"""
    task_id: str
    process: subprocess.Popen
    start_time: datetime
    command: List[str]
    status: TaskStatus
    pid: int

class TaskManager:
    """任务管理器"""
    
    def __init__(self, server_comm, config: Dict[str, Any]):
        self.server_comm = server_comm
        self.config = config
        self.logger = logging.getLogger('TaskManager')
        self.running_tasks: Dict[str, TaskProcess] = {}
        self.cancelled_tasks: set = set()
        self.paused_tasks: set = set()
        self.task_lock = threading.Lock()
        
        # 配置参数
        self.max_retries = config.get('task_manager', {}).get('max_retries', 3)
        self.retry_delay = config.get('task_manager', {}).get('retry_delay', 5)
        self.task_timeout = config.get('task_manager', {}).get('task_timeout', 3600)  # 1小时
        
        # 启动任务监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
        self.monitor_thread.start()
        
    def register_task(self, task_id: str, process: subprocess.Popen, command: List[str]) -> bool:
        """注册任务进程"""
        try:
            with self.task_lock:
                task_process = TaskProcess(
                    task_id=task_id,
                    process=process,
                    start_time=datetime.now(),
                    command=command,
                    status=TaskStatus.RUNNING,
                    pid=process.pid
                )
                self.running_tasks[task_id] = task_process
                self.logger.info(f"注册任务进程: {task_id}, PID: {process.pid}")
                return True
        except Exception as e:
            self.logger.error(f"注册任务进程失败: {e}")
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            with self.task_lock:
                if task_id in self.running_tasks:
                    task_process = self.running_tasks[task_id]
                    
                    # 标记为取消状态
                    self.cancelled_tasks.add(task_id)
                    task_process.status = TaskStatus.CANCELLED
                    
                    # 优雅终止进程
                    success = self._terminate_process(task_process.process)
                    
                    if success:
                        self.logger.info(f"任务 {task_id} 取消成功")
                        # 更新服务器状态
                        self.server_comm.update_task_status(task_id, {
                            'status': 'cancelled',
                            'cancelled_at': datetime.now().isoformat()
                        })
                        return True
                    else:
                        self.logger.error(f"任务 {task_id} 取消失败")
                        return False
                else:
                    self.logger.warning(f"任务 {task_id} 不在运行中，无法取消")
                    return False
        except Exception as e:
            self.logger.error(f"取消任务失败: {e}")
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        try:
            with self.task_lock:
                if task_id in self.running_tasks:
                    task_process = self.running_tasks[task_id]
                    
                    # 发送SIGSTOP信号暂停进程
                    os.kill(task_process.pid, signal.SIGSTOP)
                    
                    # 标记为暂停状态
                    self.paused_tasks.add(task_id)
                    task_process.status = TaskStatus.PAUSED
                    
                    self.logger.info(f"任务 {task_id} 暂停成功")
                    
                    # 更新服务器状态
                    self.server_comm.update_task_status(task_id, {
                        'status': 'paused',
                        'paused_at': datetime.now().isoformat()
                    })
                    return True
                else:
                    self.logger.warning(f"任务 {task_id} 不在运行中，无法暂停")
                    return False
        except Exception as e:
            self.logger.error(f"暂停任务失败: {e}")
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        try:
            with self.task_lock:
                if task_id in self.paused_tasks:
                    task_process = self.running_tasks[task_id]
                    
                    # 发送SIGCONT信号恢复进程
                    os.kill(task_process.pid, signal.SIGCONT)
                    
                    # 移除暂停标记
                    self.paused_tasks.remove(task_id)
                    task_process.status = TaskStatus.RUNNING
                    
                    self.logger.info(f"任务 {task_id} 恢复成功")
                    
                    # 更新服务器状态
                    self.server_comm.update_task_status(task_id, {
                        'status': 'running',
                        'resumed_at': datetime.now().isoformat()
                    })
                    return True
                else:
                    self.logger.warning(f"任务 {task_id} 不在暂停状态，无法恢复")
                    return False
        except Exception as e:
            self.logger.error(f"恢复任务失败: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        with self.task_lock:
            if task_id in self.running_tasks:
                return self.running_tasks[task_id].status
            return None
    
    def get_running_tasks(self) -> List[str]:
        """获取正在运行的任务列表"""
        with self.task_lock:
            return list(self.running_tasks.keys())
    
    def cleanup_task(self, task_id: str):
        """清理任务资源"""
        try:
            with self.task_lock:
                if task_id in self.running_tasks:
                    task_process = self.running_tasks[task_id]
                    
                    # 确保进程已终止
                    if task_process.process.poll() is None:
                        self._terminate_process(task_process.process)
                    
                    # 清理资源
                    del self.running_tasks[task_id]
                    self.cancelled_tasks.discard(task_id)
                    self.paused_tasks.discard(task_id)
                    
                    self.logger.info(f"任务 {task_id} 资源清理完成")
        except Exception as e:
            self.logger.error(f"清理任务资源失败: {e}")
    
    def _terminate_process(self, process: subprocess.Popen) -> bool:
        """优雅终止进程"""
        try:
            # 首先尝试发送SIGTERM信号
            process.terminate()
            
            # 等待进程退出
            try:
                process.wait(timeout=10)  # 等待10秒
                return True
            except subprocess.TimeoutExpired:
                # 如果10秒内没有退出，强制杀死
                self.logger.warning("进程未在10秒内退出，强制杀死")
                process.kill()
                process.wait()
                return True
                
        except Exception as e:
            self.logger.error(f"终止进程失败: {e}")
            return False
    
    def _monitor_tasks(self):
        """监控任务进程"""
        while True:
            try:
                current_time = datetime.now()
                tasks_to_cleanup = []
                
                with self.task_lock:
                    for task_id, task_process in self.running_tasks.items():
                        # 检查进程是否还存在
                        if task_process.process.poll() is not None:
                            # 进程已结束
                            return_code = task_process.process.returncode
                            
                            if return_code == 0:
                                # 任务成功完成
                                task_process.status = TaskStatus.COMPLETED
                                self.server_comm.update_task_status(task_id, {
                                    'status': 'completed',
                                    'completed_at': current_time.isoformat()
                                })
                            else:
                                # 任务失败
                                if task_id not in self.cancelled_tasks:
                                    task_process.status = TaskStatus.FAILED
                                    self.server_comm.update_task_status(task_id, {
                                        'status': 'failed',
                                        'failed_at': current_time.isoformat(),
                                        'error': f'进程退出码: {return_code}'
                                    })
                            
                            tasks_to_cleanup.append(task_id)
                        
                        # 检查任务超时
                        elif (current_time - task_process.start_time).total_seconds() > self.task_timeout:
                            self.logger.warning(f"任务 {task_id} 超时，自动取消")
                            self.cancel_task(task_id)
                            tasks_to_cleanup.append(task_id)
                
                # 清理已完成的任务
                for task_id in tasks_to_cleanup:
                    self.cleanup_task(task_id)
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                self.logger.error(f"任务监控异常: {e}")
                time.sleep(10)

class TaskRetryManager:
    """任务重试管理器"""
    
    def __init__(self, server_comm, config: Dict[str, Any]):
        self.server_comm = server_comm
        self.config = config
        self.logger = logging.getLogger('TaskRetryManager')
        self.retry_counts: Dict[str, int] = {}
        self.retry_lock = threading.Lock()
        
        # 配置参数
        self.max_retries = config.get('retry', {}).get('max_retries', 3)
        self.retry_delay = config.get('retry', {}).get('retry_delay', 5)
        self.backoff_factor = config.get('retry', {}).get('backoff_factor', 2)
    
    def should_retry(self, task_id: str, error: Exception) -> bool:
        """判断是否应该重试"""
        with self.retry_lock:
            current_retries = self.retry_counts.get(task_id, 0)
            
            if current_retries >= self.max_retries:
                self.logger.info(f"任务 {task_id} 已达到最大重试次数 {self.max_retries}")
                return False
            
            # 根据错误类型判断是否可以重试
            if self._is_retryable_error(error):
                self.retry_counts[task_id] = current_retries + 1
                return True
            
            return False
    
    def get_retry_delay(self, task_id: str) -> float:
        """获取重试延迟时间"""
        with self.retry_lock:
            retry_count = self.retry_counts.get(task_id, 0)
            return self.retry_delay * (self.backoff_factor ** retry_count)
    
    def reset_retry_count(self, task_id: str):
        """重置重试计数"""
        with self.retry_lock:
            self.retry_counts.pop(task_id, None)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可以重试"""
        # 网络相关错误可以重试
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # 临时性错误可以重试
        error_msg = str(error).lower()
        retryable_keywords = [
            'connection', 'timeout', 'network', 'temporary', 
            'busy', 'unavailable', 'refused'
        ]
        
        return any(keyword in error_msg for keyword in retryable_keywords)

class TaskValidator:
    """任务验证器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('TaskValidator')
    
    def validate_task(self, task: Dict[str, Any]) -> tuple[bool, str]:
        """验证任务配置"""
        try:
            # 检查必需字段
            required_fields = ['id', 'type', 'source_type']
            for field in required_fields:
                if field not in task:
                    return False, f"缺少必需字段: {field}"
            
            # 验证任务类型
            valid_types = ['sync', 'copy', 'mount-check', 'test-connection']
            if task['type'] not in valid_types:
                return False, f"不支持的任务类型: {task['type']}"
            
            # 验证源端类型
            valid_source_types = ['storage', 'client']
            if task['source_type'] not in valid_source_types:
                return False, f"不支持的源端类型: {task['source_type']}"
            
            # 验证存储配置
            if task['source_type'] == 'storage':
                if 'source_storage_config' not in task:
                    return False, "存储任务缺少source_storage_config"
                
                is_valid, error = self._validate_storage_config(task['source_storage_config'])
                if not is_valid:
                    return False, f"源端存储配置错误: {error}"
            
            if 'target_storage_config' in task:
                is_valid, error = self._validate_storage_config(task['target_storage_config'])
                if not is_valid:
                    return False, f"目标端存储配置错误: {error}"
            
            return True, "验证通过"
            
        except Exception as e:
            return False, f"验证异常: {str(e)}"
    
    def _validate_storage_config(self, storage_config: Dict[str, Any]) -> tuple[bool, str]:
        """验证存储配置"""
        try:
            # 检查必需字段
            required_fields = ['type', 'config']
            for field in required_fields:
                if field not in storage_config:
                    return False, f"缺少字段: {field}"
            
            storage_type = storage_config['type']
            config = storage_config['config']
            
            # 根据存储类型验证配置
            if storage_type in ['nas', 'nfs']:
                nas_fields = ['host', 'share_path']
                for field in nas_fields:
                    if field not in config:
                        return False, f"NAS配置缺少字段: {field}"
                        
            elif storage_type in ['s3', 'obs']:
                s3_fields = ['access_key', 'secret_key', 'region']
                for field in s3_fields:
                    if field not in config:
                        return False, f"S3配置缺少字段: {field}"
                        
            elif storage_type == 'local':
                if 'base_path' not in config:
                    return False, "本地存储配置缺少base_path"
            
            return True, "验证通过"
            
        except Exception as e:
            return False, f"验证异常: {str(e)}"