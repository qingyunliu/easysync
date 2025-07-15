import logging
import threading
import time
import platform
import socket
import subprocess
import requests
from datetime import datetime
from .communication import ServerCommunication
from .task_manager import TaskManager, TaskRetryManager, TaskValidator
from .enhanced_progress import EnhancedProgressTracker
from ..services.monitor_service import MonitorService
from ..services.sync_service import SyncService
from ..services.connection_checker import StorageConnectionChecker, MountChecker

class CommandService:
    def __init__(self, config, node_id, token, server_url):
        self.config = config
        self.node_id = node_id
        self.token = token
        self.server_url = server_url
        self.running = False
        self.poll_interval = config.get('command_poll_interval', 10)

    def start(self):
        self.running = True
        while self.running:
            try:
                self.poll_and_execute()
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"Command poll error: {e}")
                time.sleep(5)

    def poll_and_execute(self):
        url = f"{self.server_url}/api/agent/{self.node_id}/commands"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                commands = resp.json().get('data', [])
                for cmd in commands:
                    result = self.execute_command(cmd)
                    self.report_command_result(cmd['id'], result)
        except Exception as e:
            print(f"命令拉取失败: {e}")

    def execute_command(self, cmd):
        if cmd.get('type') == 'shell':
            try:
                completed = subprocess.run(
                    cmd['command'],
                    shell=True,
                    capture_output=True,
                    timeout=cmd.get('timeout', 60),
                    text=True
                )
                return {
                    'return_code': completed.returncode,
                    'stdout': completed.stdout,
                    'stderr': completed.stderr
                }
            except Exception as e:
                return {
                    'return_code': -1,
                    'stdout': '',
                    'stderr': str(e)
                }
        # 可扩展其它类型
        return {'return_code': -2, 'stdout': '', 'stderr': 'Unknown command type'}

    def report_command_result(self, cmd_id, result):
        url = f"{self.server_url}/api/agent/{self.node_id}/commands/{cmd_id}/result"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            requests.post(url, json={'result': result}, headers=headers, timeout=5)
        except Exception as e:
            print(f"命令结果上报失败: {e}")

class ProxyAgent:
    """代理类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger('ProxyAgent')
        self.server_comm = ServerCommunication(config)
        self.monitor_service = MonitorService(config, None, None)  # node_id/token后续赋值
        self.sync_service = SyncService(config)
        self.running = False
        self.heartbeat_thread = None
        self.task_poll_thread = None
        self.command_thread = None
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        self.task_poll_interval = self.config.get('task_poll_interval', 10)
        self.user_id = None
        self.node_id = None
        self.token = None
        self.version = self.config.get('version', '1.0.0')
        self.start_time = time.time()
        self.command_service = None
        
        # 新增功能组件
        self.task_manager = TaskManager(self.server_comm, config)
        self.task_retry_manager = TaskRetryManager(self.server_comm, config)
        self.task_validator = TaskValidator(config)
        self.progress_tracker = EnhancedProgressTracker(self.server_comm, config)
        self.connection_checker = StorageConnectionChecker(config)
        self.mount_checker = MountChecker(config)
        
        self._setup_services()

    def _setup_services(self):
        self.monitor_service.add_callback(self._on_monitor_update)
        self.sync_service.add_callback(self._on_sync_update)

    def _get_ipaddress(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        self.running = True
        # 注册节点，获取node_id和token
        self._register_node()
        # 更新monitor_service的node_id和token
        self.monitor_service.node_id = self.node_id
        self.monitor_service.token = self.token
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        # 启动监控服务
        threading.Thread(target=self.monitor_service.start, daemon=True).start()
        # 启动任务拉取线程
        self.task_poll_thread = threading.Thread(target=self._task_poll_loop, daemon=True)
        self.task_poll_thread.start()
        # 启动同步服务
        self.sync_service.start()
        # 启动命令服务
        self.command_service = CommandService(self.config, self.node_id, self.token, self.server_comm.server_url)
        self.command_thread = threading.Thread(target=self.command_service.start, daemon=True)
        self.command_thread.start()

    def stop(self):
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        if self.task_poll_thread:
            self.task_poll_thread.join(timeout=5)
        if self.command_thread:
            self.command_thread.join(timeout=5)
        self.monitor_service.stop()
        self.sync_service.stop()

    def _register_node(self):
        node_info = {
            'name': platform.node(),
            'hostname': platform.node(),
            'ipaddress': self._get_ipaddress(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'user_id': self.server_comm.user_id,
            'version': self.version
        }
        node_id = self.server_comm.register_node(node_info)
        if not node_id:
            raise Exception("Failed to register node")
        self.node_id = node_id
        self.user_id = self.server_comm.user_id
        self.token = self.server_comm.token
        self.logger.info(f"Node registered with ID: {node_id}")

    def _heartbeat_loop(self):
        while self.running:
            try:
                uptime = int(time.time() - self.start_time)
                heartbeat_info = {
                    "node_id": self.node_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": self.version,
                    "status": "online",
                    "ipaddress": self._get_ipaddress(),
                    "hostname": platform.node(),
                    "uptime": uptime
                }
                if not self.server_comm.send_heartbeat(heartbeat_info):
                    self.logger.warning("Failed to send heartbeat")
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
            time.sleep(self.heartbeat_interval)

    def _task_poll_loop(self):
        while self.running:
            try:
                # 获取分配给当前节点的任务
                tasks = self.server_comm.get_tasks()
                if tasks:
                    for task in tasks:
                        # 检查任务状态，只处理assigned状态的任务
                        if task.get('status') == 'assigned':
                            # 验证任务配置
                            is_valid, error_message = self.task_validator.validate_task(task)
                            if not is_valid:
                                self.logger.error(f"任务验证失败: {task['id']}, {error_message}")
                                self.server_comm.update_task_status(task['id'], {
                                    'status': 'failed',
                                    'error': f'任务验证失败: {error_message}'
                                })
                                continue
                            
                            # 检查是否需要连接检查
                            if task.get('type') == 'test-connection':
                                self._handle_connection_test_task(task)
                                continue
                            
                            # 检查是否需要挂载检查
                            if task.get('type') == 'mount-check':
                                self._handle_mount_check_task(task)
                                continue
                            
                            # 开始执行任务
                            self.sync_service.add_task(task)
                            
                            # 更新任务状态为running
                            self.server_comm.update_task_status(task['id'], {
                                'status': 'running',
                                'progress': 0,
                                'started_at': datetime.utcnow().isoformat()
                            })
                            
                            self.logger.info(f"Started executing task {task['id']} of type {task.get('type', 'unknown')}")
                        
                        # 处理任务取消请求
                        elif task.get('status') == 'cancel_requested':
                            self.logger.info(f"收到任务取消请求: {task['id']}")
                            success = self.task_manager.cancel_task(task['id'])
                            if success:
                                self.logger.info(f"任务 {task['id']} 取消成功")
                            else:
                                self.logger.warning(f"任务 {task['id']} 取消失败")
                        
                        # 处理任务暂停请求
                        elif task.get('status') == 'pause_requested':
                            self.logger.info(f"收到任务暂停请求: {task['id']}")
                            success = self.task_manager.pause_task(task['id'])
                            if success:
                                self.logger.info(f"任务 {task['id']} 暂停成功")
                            else:
                                self.logger.warning(f"任务 {task['id']} 暂停失败")
                        
                        # 处理任务恢复请求
                        elif task.get('status') == 'resume_requested':
                            self.logger.info(f"收到任务恢复请求: {task['id']}")
                            success = self.task_manager.resume_task(task['id'])
                            if success:
                                self.logger.info(f"任务 {task['id']} 恢复成功")
                            else:
                                self.logger.warning(f"任务 {task['id']} 恢复失败")
                            
            except Exception as e:
                self.logger.error(f"Error in task poll loop: {e}")
            time.sleep(self.task_poll_interval)

    def _handle_connection_test_task(self, task):
        """处理连接测试任务"""
        task_id = task['id']
        
        try:
            # 开始进度跟踪
            self.progress_tracker.start_task_progress(task_id, 2, ['连接测试', '完成'])
            
            # 更新任务状态为running
            self.server_comm.update_task_status(task_id, {
                'status': 'running',
                'progress': 0,
                'started_at': datetime.utcnow().isoformat()
            })
            
            # 获取存储配置
            storage_config = task.get('storage_config')
            if not storage_config:
                raise ValueError("缺少存储配置信息")
            
            # 执行连接测试
            self.progress_tracker.update_step_progress(task_id, 0, '执行连接测试', 50)
            
            result = self.connection_checker.check_storage_connection(storage_config)
            
            # 更新进度
            self.progress_tracker.update_step_progress(task_id, 1, '连接测试完成', 100)
            
            # 更新任务状态
            if result.status.value == 'success':
                self.server_comm.update_task_status(task_id, {
                    'status': 'completed',
                    'progress': 100,
                    'completed_at': datetime.utcnow().isoformat(),
                    'result': {
                        'connection_status': result.status.value,
                        'message': result.message,
                        'details': result.details,
                        'response_time': result.response_time
                    }
                })
                self.logger.info(f"连接测试任务 {task_id} 成功完成")
            else:
                self.server_comm.update_task_status(task_id, {
                    'status': 'failed',
                    'progress': 100,
                    'failed_at': datetime.utcnow().isoformat(),
                    'error': result.message,
                    'result': {
                        'connection_status': result.status.value,
                        'message': result.message,
                        'details': result.details,
                        'response_time': result.response_time
                    }
                })
                self.logger.error(f"连接测试任务 {task_id} 失败: {result.message}")
            
            # 完成进度跟踪
            self.progress_tracker.complete_task_progress(task_id, result.status.value == 'success')
            
        except Exception as e:
            self.logger.error(f"连接测试任务 {task_id} 执行异常: {e}")
            self.server_comm.update_task_status(task_id, {
                'status': 'failed',
                'progress': 0,
                'failed_at': datetime.utcnow().isoformat(),
                'error': str(e)
            })
            self.progress_tracker.complete_task_progress(task_id, False, str(e))
    
    def _handle_mount_check_task(self, task):
        """处理挂载检查任务"""
        task_id = task['id']
        
        try:
            # 开始进度跟踪
            self.progress_tracker.start_task_progress(task_id, 2, ['挂载检查', '完成'])
            
            # 更新任务状态为running
            self.server_comm.update_task_status(task_id, {
                'status': 'running',
                'progress': 0,
                'started_at': datetime.utcnow().isoformat()
            })
            
            # 获取挂载点
            mount_point = task.get('mount_point')
            if not mount_point:
                raise ValueError("缺少挂载点信息")
            
            # 执行挂载检查
            self.progress_tracker.update_step_progress(task_id, 0, '执行挂载检查', 50)
            
            result = self.mount_checker.check_mount_status(mount_point)
            
            # 更新进度
            self.progress_tracker.update_step_progress(task_id, 1, '挂载检查完成', 100)
            
            # 更新任务状态
            if result.status.value == 'success':
                self.server_comm.update_task_status(task_id, {
                    'status': 'completed',
                    'progress': 100,
                    'completed_at': datetime.utcnow().isoformat(),
                    'result': {
                        'mount_status': result.status.value,
                        'mount_point': result.mount_point,
                        'is_mounted': result.is_mounted,
                        'mount_info': result.mount_info
                    }
                })
                self.logger.info(f"挂载检查任务 {task_id} 成功完成")
            else:
                self.server_comm.update_task_status(task_id, {
                    'status': 'failed',
                    'progress': 100,
                    'failed_at': datetime.utcnow().isoformat(),
                    'error': result.error or '挂载检查失败',
                    'result': {
                        'mount_status': result.status.value,
                        'mount_point': result.mount_point,
                        'is_mounted': result.is_mounted,
                        'mount_info': result.mount_info
                    }
                })
                self.logger.error(f"挂载检查任务 {task_id} 失败: {result.error}")
            
            # 完成进度跟踪
            self.progress_tracker.complete_task_progress(task_id, result.status.value == 'success')
            
        except Exception as e:
            self.logger.error(f"挂载检查任务 {task_id} 执行异常: {e}")
            self.server_comm.update_task_status(task_id, {
                'status': 'failed',
                'progress': 0,
                'failed_at': datetime.utcnow().isoformat(),
                'error': str(e)
            })
            self.progress_tracker.complete_task_progress(task_id, False, str(e))

    def _on_monitor_update(self, metrics):
        self.logger.debug(f"Monitor update: {metrics}")

    def _on_sync_update(self, status):
        self.logger.debug(f"Sync update: {status}")

    def wait(self):
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def is_healthy(self):
        return self.running and self.heartbeat_thread and self.heartbeat_thread.is_alive() and self.task_poll_thread and self.task_poll_thread.is_alive() and self.command_thread and self.command_thread.is_alive()
    
    def get_agent_status(self):
        """获取代理状态信息"""
        try:
            return {
                'node_id': self.node_id,
                'status': 'running' if self.running else 'stopped',
                'version': self.version,
                'uptime': int(time.time() - self.start_time),
                'healthy': self.is_healthy(),
                'threads': {
                    'heartbeat': self.heartbeat_thread.is_alive() if self.heartbeat_thread else False,
                    'task_poll': self.task_poll_thread.is_alive() if self.task_poll_thread else False,
                    'command': self.command_thread.is_alive() if self.command_thread else False
                },
                'services': {
                    'monitor': self.monitor_service.is_running() if hasattr(self.monitor_service, 'is_running') else True,
                    'sync': self.sync_service.is_running() if hasattr(self.sync_service, 'is_running') else True
                },
                'task_manager': {
                    'running_tasks': len(self.task_manager.get_running_tasks()),
                    'running_task_ids': self.task_manager.get_running_tasks()
                },
                'last_heartbeat': datetime.utcnow().isoformat(),
                'config': {
                    'heartbeat_interval': self.heartbeat_interval,
                    'task_poll_interval': self.task_poll_interval,
                    'server_url': self.server_comm.server_url
                }
            }
        except Exception as e:
            self.logger.error(f"获取代理状态失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务的外部接口"""
        return self.task_manager.cancel_task(task_id)
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务的外部接口"""
        return self.task_manager.pause_task(task_id)
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务的外部接口"""
        return self.task_manager.resume_task(task_id)
    
    def get_task_progress(self, task_id: str):
        """获取任务进度的外部接口"""
        return self.progress_tracker.get_task_progress(task_id)
    
    def check_storage_connection(self, storage_config: dict):
        """检查存储连接的外部接口"""
        return self.connection_checker.check_storage_connection(storage_config)
    
    def check_mount_status(self, mount_point: str):
        """检查挂载状态的外部接口"""
        return self.mount_checker.check_mount_status(mount_point) 