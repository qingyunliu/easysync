#!/usr/bin/env python3
"""
任务管理器 - 处理任务取消、重试、状态管理等高级功能
"""

import subprocess
import threading
import time
import signal
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from ..utils.logger import get_log_manager
from ..core.communication import ServerCommunication
from ..models.task_state import TaskLogger, TaskPhase, LogLevel

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"

class TaskProcess:
    """任务进程信息"""
    
    def __init__(self, task_id: str, process: subprocess.Popen, status: TaskStatus = TaskStatus.RUNNING):
        self.task_id = task_id
        self.process = process
        self.status = status
        self.start_time = datetime.utcnow()
        self.end_time = None
        
    def complete(self, status: TaskStatus):
        """完成任务"""
        self.status = status
        self.end_time = datetime.utcnow()
        
    def get_duration(self) -> Optional[float]:
        """获取任务持续时间（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class TaskManager:
    """任务管理器 - 统一管理所有任务进程"""
    
    def __init__(self, server_comm: ServerCommunication, config: Dict[str, Any]):
        self.config = config
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('TaskManager')
        self.server_comm = server_comm
        self.task_logger = TaskLogger(server_comm)  # 任务日志管理器
        
        # 任务管理
        self.running_tasks: Dict[str, TaskProcess] = {}
        self.cancelled_tasks: set = set()
        self.paused_tasks: set = set()
        self.task_lock = threading.Lock()
        
        # 清理线程
        self.cleanup_thread = None
        self.running = False
        
    def start(self):
        """启动任务管理器"""
        if self.running:
            return
            
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
        
    def stop(self):
        """停止任务管理器"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
            
    def register_task(self, task_id: str, process: subprocess.Popen) -> bool:
        """注册任务进程
        
        Args:
            task_id: 任务ID
            process: 进程对象
            
        Returns:
            bool: 是否成功注册
        """
        try:
            with self.task_lock:
                if task_id in self.running_tasks:
                    self.logger.warning(f"任务 {task_id} 已存在，覆盖注册")
                    
                task_process = TaskProcess(task_id, process)
                self.running_tasks[task_id] = task_process
                
                self.logger.info(f"任务 {task_id} 注册成功，PID: {process.pid}")
                return True
                
        except Exception as e:
            self.logger.error(f"注册任务失败: {e}")
            return False
            
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            with self.task_lock:
                if task_id in self.running_tasks:
                    task_process = self.running_tasks[task_id]
                    
                    # 记录取消请求日志
                    self.task_logger.log_task_event(
                        task_id=task_id,
                        phase=TaskPhase.TASK_CANCELLED,
                        level=LogLevel.INFO,
                        message=f"Task '{task_id}' cancel requested"
                    )
                    
                    # 标记为取消状态
                    self.cancelled_tasks.add(task_id)
                    task_process.status = TaskStatus.CANCELLED
                    
                    # 优雅终止进程
                    success = self._terminate_process(task_process.process)
                    
                    if success:
                        self.logger.info(f"任务 {task_id} 取消成功")
                        # 记录取消完成日志
                        self.task_logger.log_task_event(
                            task_id=task_id,
                            phase=TaskPhase.TASK_CANCELLED,
                            level=LogLevel.INFO,
                            message="任务已成功取消"
                        )
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
                    # 任务不在运行中，直接上报取消状态
                    self.logger.info(f"任务 {task_id} 不在运行中，直接上报取消状态")
                    self.task_logger.log_task_event(
                        task_id=task_id,
                        phase=TaskPhase.TASK_CANCELLED,
                        level=LogLevel.INFO,
                        message="任务已取消（不在运行中）"
                    )
                    self.server_comm.update_task_status(task_id, {
                        'status': 'cancelled',
                        'cancelled_at': datetime.now().isoformat(),
                        'message': '任务已取消（不在运行中）'
                    })
                    return True
        except Exception as e:
            self.logger.error(f"取消任务失败: {e}")
            return False
            
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        try:
            with self.task_lock:
                if task_id in self.running_tasks:
                    task_process = self.running_tasks[task_id]
                    
                    # 记录暂停请求日志
                    self.task_logger.log_task_event(
                        task_id=task_id,
                        phase=TaskPhase.TASK_PAUSED,
                        level=LogLevel.INFO,
                        message=f"Task '{task_id}' pause requested"
                    )
                    
                    # 标记为暂停状态
                    self.paused_tasks.add(task_id)
                    task_process.status = TaskStatus.PAUSED
                    
                    # 暂停进程（发送SIGSTOP）
                    try:
                        task_process.process.send_signal(subprocess.SIGSTOP)
                        self.logger.info(f"任务 {task_id} 暂停成功")
                        
                        # 记录暂停完成日志
                        self.task_logger.log_task_event(
                            task_id=task_id,
                            phase=TaskPhase.TASK_PAUSED,
                            level=LogLevel.INFO,
                            message="任务已成功暂停"
                        )
                        
                        # 更新服务器状态
                        self.server_comm.update_task_status(task_id, {
                            'status': 'paused',
                            'paused_at': datetime.now().isoformat()
                        })
                        return True
                    except Exception as e:
                        self.logger.error(f"暂停任务失败: {e}")
                        return False
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
                if task_id in self.running_tasks and task_id in self.paused_tasks:
                    task_process = self.running_tasks[task_id]
                    
                    # 恢复进程（发送SIGCONT）
                    try:
                        task_process.process.send_signal(subprocess.SIGCONT)
                        self.paused_tasks.remove(task_id)
                        task_process.status = TaskStatus.RUNNING
                        
                        self.logger.info(f"任务 {task_id} 恢复成功")
                        
                        # 更新服务器状态
                        self.server_comm.update_task_status(task_id, {
                            'status': 'running',
                            'resumed_at': datetime.now().isoformat()
                        })
                        return True
                    except Exception as e:
                        self.logger.error(f"恢复任务失败: {e}")
                        return False
                else:
                    self.logger.warning(f"任务 {task_id} 不在暂停状态，无法恢复")
                    return False
                    
        except Exception as e:
            self.logger.error(f"恢复任务失败: {e}")
            return False
            
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self.task_lock:
            if task_id in self.running_tasks:
                task_process = self.running_tasks[task_id]
                return {
                    'task_id': task_id,
                    'status': task_process.status.value,
                    'pid': task_process.process.pid,
                    'start_time': task_process.start_time.isoformat(),
                    'duration': task_process.get_duration()
                }
        return None
        
    def list_running_tasks(self) -> List[Dict[str, Any]]:
        """列出所有运行中的任务"""
        with self.task_lock:
            return [
                {
                    'task_id': task_id,
                    'status': task_process.status.value,
                    'pid': task_process.process.pid,
                    'start_time': task_process.start_time.isoformat(),
                    'duration': task_process.get_duration()
                }
                for task_id, task_process in self.running_tasks.items()
            ]
            
    def _terminate_process(self, process: subprocess.Popen) -> bool:
        """终止进程"""
        try:
            # 尝试优雅终止
            process.terminate()
            
            # 等待进程结束
            try:
                process.wait(timeout=10)
                return True
            except subprocess.TimeoutExpired:
                # 如果超时，强制杀死
                self.logger.warning(f"进程 {process.pid} 优雅终止超时，强制杀死")
                process.kill()
                process.wait()
                return True
                
        except Exception as e:
            self.logger.error(f"终止进程失败: {e}")
            return False
            
    def _cleanup_loop(self):
        """清理循环 - 检查已结束的进程"""
        while self.running:
            try:
                with self.task_lock:
                    completed_tasks = []
                    
                    for task_id, task_process in self.running_tasks.items():
                        # 检查进程是否已结束
                        if task_process.process.poll() is not None:
                            # 进程已结束
                            return_code = task_process.process.returncode
                            
                            if return_code == 0:
                                task_process.complete(TaskStatus.COMPLETED)
                                self.logger.info(f"任务 {task_id} 已完成")
                            else:
                                task_process.complete(TaskStatus.FAILED)
                                self.logger.error(f"任务 {task_id} 失败，返回码: {return_code}")
                                
                            completed_tasks.append(task_id)
                            
                    # 移除已完成的任务
                    for task_id in completed_tasks:
                        del self.running_tasks[task_id]
                        
                # 等待一段时间再检查
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"清理循环异常: {e}")
                time.sleep(5)

class TaskRetryManager:
    """任务重试管理器"""
    
    def __init__(self, server_comm, config: Dict[str, Any]):
        self.server_comm = server_comm
        self.config = config
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('TaskRetryManager')
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
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('TaskValidator')
    
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
                nas_fields = ['server']
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