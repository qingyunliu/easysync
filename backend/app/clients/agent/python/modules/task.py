import logging
import threading
import subprocess
import shutil
import os
import time
import queue
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: int = 5, 
                    exceptions: tuple = (Exception,)):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"操作失败，将在 {delay} 秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}"
                        )
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

class TaskError(Exception):
    """任务执行错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}

class TaskManager:
    def __init__(self, sio, user_id: str, client_id: str):
        self.sio = sio
        self.user_id = user_id
        self.client_id = client_id
        self.current_task = None
        self._task_lock = threading.Lock()
        self._max_retries = 3
        self._retry_delay = 5
        self._running = False
        self._stop_event = threading.Event()
        self._task_queue = queue.Queue()
        self._worker_thread = None
        
    def start(self):
        """启动任务管理器"""
        if self._running:
            logger.warning("任务管理器已经在运行")
            return
            
        self._running = True
        self._stop_event.clear()
        
        # 启动工作线程
        self._worker_thread = threading.Thread(target=self._worker_loop)
        self._worker_thread.daemon = True
        self._worker_thread.start()
        
        logger.info("任务管理器已启动")
        
    def stop(self):
        """停止任务管理器"""
        if not self._running:
            logger.warning("任务管理器未运行")
            return
            
        self._running = False
        self._stop_event.set()
        
        # 等待工作线程结束
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
            
        # 清空任务队列
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                break
                
        logger.info("任务管理器已停止")
        
    def _worker_loop(self):
        """工作线程主循环"""
        while self._running and not self._stop_event.is_set():
            try:
                # 从队列获取任务
                task_data = self._task_queue.get(timeout=1)
                if task_data is None:
                    continue
                    
                # 执行任务
                self.execute_task(task_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程发生错误: {e}")
                
    def execute_task(self, task_data: Dict[str, Any]):
        """执行任务"""
        with self._task_lock:
            if self.current_task is not None:
                logger.warning("已有任务正在执行，将新任务加入队列")
                self._task_queue.put(task_data)
                return
                
            self.current_task = task_data
            task_id = task_data.get('id')
            
            try:
                # 发送任务开始通知
                self._send_task_progress(task_id, 0, 'started')
                
                # 执行任务
                result = self._do_execute_task(task_data)
                
                # 发送任务完成通知
                self._send_task_progress(task_id, 100, 'completed', result)
                
            except TaskError as e:
                logger.error(f"任务执行失败: {e}")
                self._send_task_progress(
                    task_id, 
                    0, 
                    'failed', 
                    {'error': str(e), 'details': e.details}
                )
            except Exception as e:
                logger.error(f"任务执行发生未知错误: {e}")
                self._send_task_progress(
                    task_id, 
                    0, 
                    'failed', 
                    {'error': str(e), 'type': type(e).__name__}
                )
            finally:
                self.current_task = None
                # 检查队列中是否有待执行的任务
                if not self._task_queue.empty():
                    next_task = self._task_queue.get_nowait()
                    if next_task:
                        self.execute_task(next_task)
                
    def _do_execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """实际执行任务的逻辑"""
        task_type = task_data.get('type')
        task_params = task_data.get('params', {})
        
        try:
            if task_type == 'command':
                return self._execute_command(task_params)
            elif task_type == 'file_sync':
                return self._sync_files(task_params)
            else:
                raise TaskError(f"未知的任务类型: {task_type}")
        except Exception as e:
            if not isinstance(e, TaskError):
                raise TaskError(f"执行任务时发生错误: {str(e)}", {'task_type': task_type})
            raise
            
    @retry_on_failure(max_retries=3, delay=5)
    def _execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令任务"""
        command = params.get('command')
        timeout = params.get('timeout', 300)  # 默认超时时间5分钟
        working_dir = params.get('working_dir', None)
        
        if not command:
            raise TaskError("命令不能为空")
            
        try:
            # 准备执行环境
            env = os.environ.copy()
            if 'env' in params:
                env.update(params['env'])
                
            # 执行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env=env
            )
            
            # 等待命令执行完成或超时
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise TaskError(
                    f"命令执行超时: {command}",
                    {'timeout': timeout, 'command': command}
                )
                
            # 处理执行结果
            result = {
                'return_code': return_code,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore')
            }
            
            if return_code != 0:
                raise TaskError(
                    f"命令执行失败: {stderr.decode('utf-8', errors='ignore')}",
                    {'return_code': return_code, 'command': command}
                )
                
            return result
            
        except subprocess.SubprocessError as e:
            raise TaskError(f"执行命令时发生子进程错误: {e}", {'command': command})
        except Exception as e:
            raise TaskError(f"执行命令时发生未知错误: {e}", {'command': command})
            
    @retry_on_failure(max_retries=3, delay=5)
    def _sync_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件同步任务"""
        source = params.get('source')
        target = params.get('target')
        exclude = params.get('exclude', [])
        include = params.get('include', ['*'])
        
        if not source or not target:
            raise TaskError("源路径和目标路径不能为空")
            
        try:
            source_path = Path(source)
            target_path = Path(target)
            
            # 验证源目录
            if not source_path.exists():
                raise TaskError(f"源目录不存在: {source}")
            if not source_path.is_dir():
                raise TaskError(f"源路径不是目录: {source}")
                
            # 确保目标目录存在
            try:
                target_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise TaskError(f"创建目标目录失败: {e}", {'target': target})
                
            # 获取需要同步的文件列表
            files_to_sync = self._get_files_to_sync(source_path, include, exclude)
            
            if not files_to_sync:
                raise TaskError("没有找到需要同步的文件", {
                    'source': source,
                    'include': include,
                    'exclude': exclude
                })
                
            # 同步文件
            synced_files = []
            total_files = len(files_to_sync)
            failed_files = []
            
            for i, file_path in enumerate(files_to_sync, 1):
                try:
                    relative_path = file_path.relative_to(source_path)
                    target_file = target_path / relative_path
                    
                    # 确保目标目录存在
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(file_path, target_file)
                    synced_files.append(str(relative_path))
                    
                    # 更新进度
                    progress = int((i / total_files) * 100)
                    self._send_task_progress(
                        self.current_task['id'],
                        progress,
                        'in_progress',
                        {'current_file': str(relative_path)}
                    )
                except Exception as e:
                    logger.error(f"同步文件失败: {file_path} - {e}")
                    failed_files.append({
                        'file': str(file_path),
                        'error': str(e)
                    })
                    
            if failed_files:
                raise TaskError(
                    "部分文件同步失败",
                    {'failed_files': failed_files, 'total_files': total_files}
                )
                
            return {
                'synced_files': synced_files,
                'total_files': total_files
            }
            
        except TaskError:
            raise
        except Exception as e:
            raise TaskError(f"文件同步失败: {e}", {
                'source': source,
                'target': target
            })
            
    def _get_files_to_sync(self, source_path: Path, include: List[str], exclude: List[str]) -> List[Path]:
        """获取需要同步的文件列表"""
        files = []
        
        try:
            for pattern in include:
                for file_path in source_path.rglob(pattern):
                    if file_path.is_file():
                        # 检查是否在排除列表中
                        if not any(file_path.match(exclude_pattern) for exclude_pattern in exclude):
                            files.append(file_path)
        except Exception as e:
            raise TaskError(f"获取文件列表失败: {e}")
            
        return files
        
    def _send_task_progress(self, task_id: str, progress: int, status: str, 
                          result: Optional[Dict[str, Any]] = None):
        """发送任务进度"""
        try:
            progress_data = {
                'task_id': task_id,
                'user_id': self.user_id,
                'client_id': self.client_id,
                'progress': progress,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            if result is not None:
                progress_data['result'] = result
                
            self.sio.emit('task_progress', progress_data)
            logger.debug(f"发送任务进度: {progress_data}")
        except Exception as e:
            logger.error(f"发送任务进度失败: {e}") 