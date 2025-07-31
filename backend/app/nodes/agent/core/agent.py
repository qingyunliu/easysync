import threading
import time
import platform
import socket
import subprocess
import requests
import os
from datetime import datetime
from .communication import ServerCommunication
from .task_manager import TaskManager, TaskRetryManager, TaskValidator
from .enhanced_progress import EnhancedProgressTracker
from ..services.monitor_service import MonitorService
from ..services.sync_service import SyncService
from ..services.connection_checker import StorageConnectionChecker, MountChecker
from ..provider.nas import NASProvider
from ..provider.s3 import S3Provider
from ..utils.logger import get_log_manager

class ProxyAgent:
    """代理类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = get_log_manager().get_logger('ProxyAgent')
        self.server_comm = ServerCommunication(config)
        self.monitor_service = MonitorService(config, None, None)  # node_id/token后续赋值
        self.sync_service = SyncService(config)
        self.running = False
        self.heartbeat_thread = None
        self.task_poll_thread = None
        self.command_poll_thread = None
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        self.task_poll_interval = self.config.get('task_poll_interval', 10)
        self.command_interval = self.config.get('command_interval', 0.5) 
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
        # 启动实时命令轮询线程
        self.command_poll_thread = threading.Thread(target=self._command_poll_loop, daemon=True)
        self.command_poll_thread.start()
        # 启动同步服务
        self.sync_service.start()

    def stop(self):
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        if self.task_poll_thread:
            self.task_poll_thread.join(timeout=5)
        if self.command_poll_thread:
            self.command_poll_thread.join(timeout=5)
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
            'node_id': self.server_comm.node_id,
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
                            
                            # 检查是否需要存储操作
                            if task.get('type') == 'storage-operation':
                                self._handle_storage_operation_task(task)
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

    def _command_poll_loop(self):
        """实时命令轮询循环"""
        while self.running:
            try:
                # 获取待执行的实时命令
                commands = self.server_comm.get_realtime_commands()
                for command in commands:
                    self._execute_realtime_command(command)
            except Exception as e:
                self.logger.error(f"Error in command poll loop: {e}")
            time.sleep(self.command_interval)

    def _execute_realtime_command(self, command):
        """执行实时命令"""
        command_id = command['id']
        command_type = command['command_type']
        params = command['params']
        
        self.logger.info(f"执行实时命令: {command_id}, 类型: {command_type}")
        
        try:
            # 更新命令状态为执行中
            self.logger.info(f"更新命令状态为执行中: {command_id}")
            success = self.server_comm.update_command_status(command_id, {
                'status': 'executing',
                'started_at': datetime.utcnow().isoformat()
            })
            
            if not success:
                self.logger.error(f"更新命令状态为执行中失败: {command_id}")
                return
            
            # 根据命令类型执行相应的操作
            result = None
            if command_type == 'test_connection':
                result = self._execute_test_connection(params)
            elif command_type == 'get_stats':
                result = self._execute_get_stats(params)
            elif command_type == 'list_objects':
                result = self._execute_list_objects(params)
            elif command_type == 'list_buckets':
                result = self._execute_list_buckets(params)
            elif command_type == 'download_file':
                result = self._execute_download_file(params)
            elif command_type == 'upload_file':
                result = self._execute_upload_file(params)
            else:
                raise ValueError(f"不支持的命令类型: {command_type}")
            
            # 更新命令状态为完成
            self.logger.info(f"更新命令状态为完成: {command_id}, 结果: {result}")
            success = self.server_comm.update_command_status(command_id, {
                'status': 'completed',
                'result': result,
                'completed_at': datetime.utcnow().isoformat()
            })
            
            if not success:
                self.logger.error(f"更新命令状态为完成失败: {command_id}")
            else:
                self.logger.info(f"实时命令执行完成: {command_id}")
            
        except Exception as e:
            self.logger.error(f"实时命令执行失败: {command_id}, 错误: {str(e)}")
            
            # 更新命令状态为失败
            try:
                success = self.server_comm.update_command_status(command_id, {
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.utcnow().isoformat()
                })
                
                if not success:
                    self.logger.error(f"更新命令状态为失败也失败了: {command_id}")
            except Exception as update_error:
                self.logger.error(f"更新命令状态为失败时发生异常: {command_id}, 错误: {str(update_error)}")

    def _execute_test_connection(self, params):
        """执行连接测试"""
        storage_config = params.get('storage_config')
        if not storage_config:
            raise ValueError("缺少存储配置")
        
        result = self.connection_checker.check_storage_connection(storage_config)
        return {
            'status': result.status.value,
            'message': result.message,
            'response_time': result.response_time,
            'details': result.details,
            'check_time': result.check_time.isoformat()
        }

    def _execute_get_stats(self, params):
        """获取存储统计信息"""
        storage_config = params.get('storage_config')
        if not storage_config:
            raise ValueError("缺少存储配置")
        
        return self._execute_storage_operation(storage_config, 'get_stats', {})

    def _execute_list_objects(self, params):
        """获取对象列表"""
        storage_config = params.get('storage_config')
        if not storage_config:
            raise ValueError("缺少存储配置")
        
        storage_type = storage_config.get('type', '').lower()
        
        # 对于NAS类型，需要处理挂载点
        if storage_type in ['nas', 'nfs']:
            return self._execute_nas_list_objects(params)
        else:
            # 对于S3/OBS类型，使用原有逻辑
            operation_params = {
                'bucket': params.get('bucket', ''),
                'prefix': params.get('prefix', ''),
                'page': params.get('page', 1),
                'page_size': params.get('page_size', 20)
            }
            return self._execute_storage_operation(storage_config, 'list_objects', operation_params)
    
    def _execute_nas_list_objects(self, params):
        """执行NAS存储的对象列表操作"""
        storage_config = params.get('storage_config')
        path = params.get('path', '')
        page = params.get('page', 1)
        page_size = params.get('page_size', 20)
        
        # 检查是否有指定的挂载点
        mount_point = params.get('mount_point')
        
        if mount_point:
            # 有指定挂载点，检查挂载状态
            mount_result = self.mount_checker.check_mount_status(mount_point)
            
            if mount_result.is_mounted:
                # 检查挂载点是否匹配当前存储
                mount_info = mount_result.mount_info
                if self._is_mount_point_matches_storage(mount_point, storage_config):
                    # 挂载点匹配，直接使用
                    return self._list_objects_from_mount_point(mount_point, path, page, page_size)
                else:
                    # 挂载点不匹配，返回错误信息
                    return {
                        'error': f'挂载点 {mount_point} 已被其他存储使用',
                        'mount_info': mount_info,
                        'suggested_action': 'unmount_existing'
                    }
            else:
                # 挂载点存在但未挂载，执行挂载
                mount_result = self.mount_checker.mount_storage(mount_point, storage_config)
                if mount_result.status.value == 'success':
                    return self._list_objects_from_mount_point(mount_point, path, page, page_size)
                else:
                    return {
                        'error': f'挂载失败: {mount_result.error}',
                        'mount_point': mount_point
                    }
        else:
            # 没有指定挂载点，自动生成并挂载
            import tempfile
            import uuid
            
            # 生成唯一的挂载点
            mount_point = f"/tmp/easysync_nas_{uuid.uuid4().hex[:8]}"
            
            # 执行挂载
            mount_result = self.mount_checker.mount_storage(mount_point, storage_config)
            
            if mount_result.status.value == 'success':
                try:
                    # 获取文件列表
                    result = self._list_objects_from_mount_point(mount_point, path, page, page_size)
                    
                    # 在结果中添加挂载点信息，供服务端保存
                    result['mount_point'] = mount_point
                    result['auto_mounted'] = True
                    
                    return result
                except Exception as e:
                    # 清理挂载点
                    try:
                        import subprocess
                        subprocess.run(['umount', mount_point], check=True)
                        os.rmdir(mount_point)
                    except:
                        pass
                    raise e
            else:
                return {
                    'error': f'自动挂载失败: {mount_result.error}',
                    'mount_point': mount_point
                }
    
    def _is_mount_point_matches_storage(self, mount_point: str, storage_config: dict) -> bool:
        """检查挂载点是否匹配当前存储配置"""
        try:
            mount_info = self.mount_checker._get_mount_info(mount_point)
            if not mount_info:
                return False
            
            config = storage_config.get('config', {})
            server = config.get('server', '')
            share_path = config.get('path', '')
            
            # 检查挂载的设备是否匹配
            mount_device = mount_info.get('device', '')
            
            if config.get('protocol', '').lower() in ['nfs', 'nas']:
                # NFS格式：server:share_path
                expected_device = f"{server}:{share_path}"
            else:
                # SMB格式：//server/share_path
                expected_device = f"//{server}/{share_path}"
            
            return mount_device == expected_device
            
        except Exception as e:
            self.logger.error(f"检查挂载点匹配失败: {e}")
            return False
    
    def _list_objects_from_mount_point(self, mount_point: str, path: str, page: int, page_size: int) -> dict:
        """从挂载点获取文件列表"""
        try:
            # 构建完整路径
            full_path = os.path.join(mount_point, path.lstrip('/'))
            
            if not os.path.exists(full_path):
                raise ValueError(f"路径 {path} 不存在")
            
            # 获取所有对象
            objects = []
            
            try:
                items = os.listdir(full_path)
            except PermissionError:
                raise ValueError(f"没有权限访问路径 {path}")
            
            for item in items:
                item_path = os.path.join(full_path, item)
                rel_path = os.path.join(path, item) if path else item
                
                try:
                    stat = os.stat(item_path)
                    
                    if os.path.isdir(item_path):
                        objects.append({
                            'name': item,
                            'path': rel_path,
                            'type': 'directory',
                            'modified_time': datetime.utcnow().fromtimestamp(stat.st_mtime).isoformat()
                        })
                    else:
                        objects.append({
                            'name': item,
                            'path': rel_path,
                            'size': stat.st_size,
                            'modified_time': datetime.utcnow().fromtimestamp(stat.st_mtime).isoformat(),
                            'type': 'file'
                        })
                except (OSError, PermissionError):
                    continue
            
            # 实现分页
            total_count = len(objects)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            # 确保页码有效
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            
            # 获取当前页的数据
            paginated_objects = objects[start_index:end_index]
            
            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                'objects': paginated_objects,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev,
                    'start_index': start_index + 1 if total_count > 0 else 0,
                    'end_index': min(end_index, total_count)
                },
                'mount_point': mount_point
            }
            
        except Exception as e:
            raise ValueError(f"获取文件列表失败: {str(e)}")

    def _execute_list_buckets(self, params):
        """获取存储桶列表"""
        storage_config = params.get('storage_config')
        if not storage_config:
            raise ValueError("缺少存储配置")
        
        operation_params = {
            'page': params.get('page', 1),
            'page_size': params.get('page_size', 20)
        }
        
        return self._execute_storage_operation(storage_config, 'list_buckets', operation_params)

    def _execute_download_file(self, params):
        """下载文件"""
        storage_config = params.get('storage_config')
        if not storage_config:
            raise ValueError("缺少存储配置")
        
        operation_params = {
            'bucket': params.get('bucket', ''),
            'file_path': params.get('file_path', ''),
        }
        
        return self._execute_storage_operation(storage_config, 'download_file', operation_params)

    def _execute_upload_file(self, params):

        storage_config = params.get('storage_config')
        if not storage_config:
            raise ValueError("缺少存储配置")
        
        operation_params = {
            'bucket': params.get('bucket', ''),
            'file_path': params.get('file_path', ''),
        }
        
        return self._execute_storage_operation(storage_config, 'upload_file', operation_params)

    def _execute_storage_operation(self, storage_config, operation, params):
        """执行存储操作"""
        storage_type = storage_config.get('type')
        config = storage_config.get('config', {})
        
        # 根据存储类型创建提供者
        if storage_type == 'nas':
            provider = NASProvider(config)
        elif storage_type in ['s3', 'obs']:
            provider = S3Provider(config)
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        
        # 根据操作类型执行相应的方法
        if operation == 'get_stats':
            return provider.get_stats()
        elif operation == 'list_buckets':
            page = params.get('page', 1)
            page_size = params.get('page_size', 20)
            return provider.list_buckets(page, page_size)
        elif operation == 'list_objects':
            bucket = params.get('bucket', '')
            prefix = params.get('prefix', '')
            page = params.get('page', 1)
            page_size = params.get('page_size', 20)
            return provider.list_objects(bucket, prefix, page, page_size)
        elif operation == 'download_object':
            bucket = params.get('bucket', '')
            key = params.get('key', '')
            return provider.download_file_to_memory(bucket, key)
        elif operation == 'download_file':
            file_path = params.get('file_path', '')
            target_path = params.get('target_path', '')
            return provider.download_file(file_path, target_path)
        elif operation == 'upload_file':
            file_path = params.get('file_path', '')
            target_path = params.get('target_path', '')
            return provider.upload_file(file_path, target_path)
        else:
            raise ValueError(f"不支持的操作类型: {operation}")

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
            
            # 获取存储配置 - 从 options 中获取
            storage_config = task.get('options', {}).get('storage_config')
            if not storage_config:
                raise ValueError("缺少存储配置信息")
            
            self.logger.info(f"开始执行连接测试任务 {task_id}, 存储类型: {storage_config.get('type')}")
            
            # 执行连接测试
            self.progress_tracker.update_step_progress(task_id, 0, '执行连接测试', 50)
            
            result = self.connection_checker.check_storage_connection(storage_config)
            
            # 更新进度
            self.progress_tracker.update_step_progress(task_id, 1, '连接测试完成', 100)
            
            # 更新任务状态为completed
            self.server_comm.update_task_status(task_id, {
                'status': 'completed',
                'progress': 100,
                'completed_at': datetime.utcnow().isoformat(),
                'result': {
                    'status': result.status.value,
                    'message': result.message,
                    'details': result.details,
                    'check_time': result.check_time.isoformat(),
                    'response_time': result.response_time
                }
            })
            
            self.logger.info(f"连接测试任务 {task_id} 完成")
            
        except Exception as e:
            self.logger.error(f"连接测试任务 {task_id} 失败: {str(e)}")
            
            # 更新任务状态为failed
            self.server_comm.update_task_status(task_id, {
                'status': 'failed',
                'progress': 0,
                'failed_at': datetime.utcnow().isoformat(),
                'error': str(e)
            })

    def _handle_storage_operation_task(self, task):
        """处理存储操作任务"""
        task_id = task['id']
        
        try:
            # 开始进度跟踪
            self.progress_tracker.start_task_progress(task_id, 2, ['存储操作', '完成'])
            
            # 更新任务状态为running
            self.server_comm.update_task_status(task_id, {
                'status': 'running',
                'progress': 0,
                'started_at': datetime.utcnow().isoformat()
            })
            
            # 获取任务参数
            options = task.get('options', {})
            storage_config = options.get('storage_config')
            operation = options.get('operation')
            params = options.get('params', {})
            
            if not storage_config or not operation:
                raise ValueError("缺少存储配置或操作类型")
            
            self.logger.info(f"开始执行存储操作任务 {task_id}, 操作: {operation}")
            
            # 执行存储操作
            self.progress_tracker.update_step_progress(task_id, 0, f'执行{operation}操作', 50)
            
            # 根据操作类型执行相应的存储操作
            result = self._execute_storage_operation(storage_config, operation, params)
            
            # 更新进度
            self.progress_tracker.update_step_progress(task_id, 1, '存储操作完成', 100)
            
            # 更新任务状态为completed
            self.server_comm.update_task_status(task_id, {
                'status': 'completed',
                'progress': 100,
                'completed_at': datetime.utcnow().isoformat(),
                'result': result
            })
            
            self.logger.info(f"存储操作任务 {task_id} 完成")
            
        except Exception as e:
            self.logger.error(f"存储操作任务 {task_id} 失败: {str(e)}")
            
            # 更新任务状态为failed
            self.server_comm.update_task_status(task_id, {
                'status': 'failed',
                'progress': 0,
                'failed_at': datetime.utcnow().isoformat(),
                'error': str(e)
            })
    
    def _handle_mount_check_task(self, task):
        """处理挂载检查任务"""
        task_id = task['id']
        
        try:
            # 开始进度跟踪
            self.progress_tracker.start_task_progress(task_id, 3, ['检查挂载状态', '执行挂载', '完成'])
            
            # 更新任务状态为running
            self.server_comm.update_task_status(task_id, {
                'status': 'running',
                'progress': 0,
                'started_at': datetime.utcnow().isoformat()
            })
            
            # 获取挂载点和存储配置
            mount_point = task.get('mount_point')
            storage_config = task.get('source_storage_config', {}).get('config', {})
            
            if not mount_point:
                raise ValueError("缺少挂载点信息")
            if not storage_config:
                raise ValueError("缺少存储配置信息")
            
            # 步骤1：检查当前挂载状态
            self.progress_tracker.update_step_progress(task_id, 0, '检查挂载状态', 30)
            result = self.mount_checker.check_mount_status(mount_point)
            
            # 如果已经挂载且可访问，直接返回成功
            if result.status.value == 'success':
                self.progress_tracker.update_step_progress(task_id, 2, '挂载检查完成', 100)
                self.server_comm.update_task_status(task_id, {
                    'status': 'completed',
                    'progress': 100,
                    'completed_at': datetime.utcnow().isoformat(),
                    'result': {
                        'mount_status': result.status.value,
                        'mount_point': result.mount_point,
                        'is_mounted': result.is_mounted,
                        'mount_info': result.mount_info,
                        'action': 'already_mounted'
                    }
                })
                self.logger.info(f"挂载检查任务 {task_id} 成功完成：已挂载")
                self.progress_tracker.complete_task_progress(task_id, True)
                return
            
            # 步骤2：尝试挂载
            self.progress_tracker.update_step_progress(task_id, 1, '执行挂载操作', 70)
            mount_result = self.mount_checker.mount_storage(mount_point, storage_config)
            
            if mount_result.status.value == 'success':
                # 步骤3：验证挂载结果
                self.progress_tracker.update_step_progress(task_id, 2, '验证挂载结果', 100)
                verify_result = self.mount_checker.check_mount_status(mount_point)
                
                if verify_result.status.value == 'success':
                    self.server_comm.update_task_status(task_id, {
                        'status': 'completed',
                        'progress': 100,
                        'completed_at': datetime.utcnow().isoformat(),
                        'result': {
                            'mount_status': verify_result.status.value,
                            'mount_point': verify_result.mount_point,
                            'is_mounted': verify_result.is_mounted,
                            'mount_info': verify_result.mount_info,
                            'action': 'mounted_successfully'
                        }
                    })
                    self.logger.info(f"挂载检查任务 {task_id} 成功完成：挂载成功")
                    self.progress_tracker.complete_task_progress(task_id, True)
                else:
                    self.server_comm.update_task_status(task_id, {
                        'status': 'failed',
                        'progress': 100,
                        'failed_at': datetime.utcnow().isoformat(),
                        'error': f"挂载后验证失败: {verify_result.error}",
                        'result': {
                            'mount_status': verify_result.status.value,
                            'mount_point': verify_result.mount_point,
                            'is_mounted': verify_result.is_mounted,
                            'mount_info': verify_result.mount_info,
                            'action': 'mount_verification_failed'
                        }
                    })
                    self.logger.error(f"挂载检查任务 {task_id} 失败：挂载后验证失败")
                    self.progress_tracker.complete_task_progress(task_id, False, verify_result.error)
            else:
                self.server_comm.update_task_status(task_id, {
                    'status': 'failed',
                    'progress': 100,
                    'failed_at': datetime.utcnow().isoformat(),
                    'error': f"挂载失败: {mount_result.error}",
                    'result': {
                        'mount_status': mount_result.status.value,
                        'mount_point': mount_point,
                        'is_mounted': False,
                        'mount_info': {},
                        'action': 'mount_failed'
                    }
                })
                self.logger.error(f"挂载检查任务 {task_id} 失败：挂载失败")
                self.progress_tracker.complete_task_progress(task_id, False, mount_result.error)
            
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
        return self.running and self.heartbeat_thread and self.heartbeat_thread.is_alive() and self.task_poll_thread and self.task_poll_thread.is_alive() and self.command_poll_thread and self.command_poll_thread.is_alive()
    
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
                    'command': self.command_poll_thread.is_alive() if self.command_poll_thread else False
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