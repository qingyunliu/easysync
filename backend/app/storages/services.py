from typing import Dict, Any, List, Type, Optional
from backend.app.models.storage import Storage
from backend.app.storages.provider.base import StorageProvider
from backend.app.storages.provider.nas import NASProvider
from backend.app.storages.provider.s3 import S3Provider
from backend import db
from flask import g
from backend.app.tasks.service import TaskService
from backend.app.commands.service import RealTimeCommandService
from backend.app.notifications.services import NotificationService
import logging

logger = logging.getLogger(__name__)

# 存储相关的实时命令服务
class StorageRealTimeService:
    """存储实时服务"""
    
    def __init__(self):
        self.command_service = RealTimeCommandService()
    
    def test_connection_realtime(self, storage_id: str, node_id: str) -> Dict[str, Any]:
        """实时测试存储连接
        
        Args:
            storage_id: 存储ID
            node_id: 节点ID
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 构建测试参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            }
        }
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=node_id,
            command_type='test_connection',
            params=params,
            timeout=30
        )
    
    def get_storage_stats_realtime(self, storage_id: str, node_id: str = None) -> Dict[str, Any]:
        """实时获取存储统计信息
        
        Args:
            storage_id: 存储ID
            node_id: 节点ID（可选，如果不指定则使用存储绑定的节点）
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            }
        }
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='get_stats',
            params=params,
            timeout=300
        )
    
    def list_objects_realtime(self, storage_id: str, bucket: str = '', prefix: str = '', page: int = 1, 
                              page_size: int = 20, node_id: str = None) -> dict:
        """
        实时获取对象存储 objects 列表（S3/OBS）
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}

        # 只支持S3/OBS
        if storage.type not in ['s3', 'obs']:
            return {'status': 'error', 'message': '仅支持对象存储类型'}

        # 选定目标节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}

        # 构造参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            },
            'bucket': bucket or storage.config.get('bucket', ''),
            'prefix': prefix,
            'page': page,
            'page_size': page_size
        }

        # 发起实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='list_objects',
            params=params,
            timeout=30
        )
    
    def list_files_realtime(self, storage_id: str, path: str = '', page: int = 1, 
                            page_size: int = 20, node_id: str = None) -> Dict[str, Any]:
        """实时获取文件列表
        
        Args:
            storage_id: 存储ID
            path: 路径
            page: 页码
            page_size: 每页大小
            node_id: 节点ID（可选）
            
        Returns:
            Dict[str, Any]: 文件列表
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            },
            'path': path,
            'page': page,
            'page_size': page_size
        }
        
        # 对于NAS存储，添加挂载点信息和完整配置
        if storage.type in ['nas', 'nfs']:
            mount_point = storage.config.get('mount_point')
            if mount_point:
                params['mount_point'] = mount_point
            
            # 确保NFS必要的配置字段存在
            config = storage.config
            nas_config = {
                'server': config.get('server') or config.get('host'),
                'host': config.get('host') or config.get('server'),
                'path': config.get('path') or config.get('share_path'),
                'share_path': config.get('share_path') or config.get('path'),
                'protocol': config.get('protocol', 'nfs'),
                'username': config.get('username', ''),
                'password': config.get('password', ''),
                'options': config.get('options', ''),
                'version': config.get('version', '3')
            }
            # 更新storage_config中的config部分
            params['storage_config']['config'].update(nas_config)
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='list_objects',
            params=params,
            timeout=30
        )
    
    def list_buckets_realtime(self, storage_id: str, page: int = 1, page_size: int = 20, 
                            node_id: str = None) -> Dict[str, Any]:
        """实时获取存储桶列表（仅适用于S3/OBS）
        
        Args:
            storage_id: 存储ID
            page: 页码
            page_size: 每页大小
            node_id: 节点ID（可选）
            
        Returns:
            Dict[str, Any]: 存储桶列表
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        if storage.type not in ['s3', 'obs']:
            return {'status': 'error', 'message': '该存储类型不支持存储桶操作'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            },
            'page': page,
            'page_size': page_size
        }
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='list_buckets',
            params=params,
            timeout=30
        )
    
    def download_file_realtime(self, storage_id: str, path: str, bucket: str = '', 
                             node_id: str = None) -> Dict[str, Any]:
        """实时下载文件
        
        Args:
            storage_id: 存储ID
            file_path: 文件路径
            bucket: 存储桶（S3/OBS用）
            node_id: 节点ID（可选）
            
        Returns:
            Dict[str, Any]: 下载结果
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            },
            'path': path,
            'bucket': bucket
        }
        
        # 执行实时命令（下载可能耗时较长）
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='download_file',
            params=params,
            timeout=60  # 下载允许更长时间
        )
    
    def check_mount_status_realtime(self, storage_id: str, node_id: str = None) -> Dict[str, Any]:
        """实时检查挂载状态"""
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            }
        }

        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='mount_check',
            params=params,
            timeout=30
        )

class StorageService:
    """存储服务类"""
    
    PROVIDER_MAP = {
        'nas': NASProvider,
        's3': S3Provider,
        'obs': S3Provider  # OBS 使用 S3 提供者
    }
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def get_provider_class(self, storage_type: str) -> Type[StorageProvider]:
        """获取存储提供者类"""
        if storage_type not in self.PROVIDER_MAP:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        return self.PROVIDER_MAP[storage_type]
    
    def create_storage(self, name: str, type: str, config: Dict[str, Any], node_id: str = None) -> Storage:
        """创建存储节点"""
        try:
            # 验证存储类型
            self.get_provider_class(type)
            
            storage = Storage(
                name=name,
                type=type,
                config=config,
                user_id=g.user.id,
                node_id=node_id  # 添加节点ID绑定
            )
            db.session.add(storage)
            db.session.commit()
            
            # 发送创建成功通知
            self._send_storage_notification(
                storage, 
                'created', 
                f'存储 {name} 已成功创建',
                {'storage_type': type, 'node_id': node_id}
            )
            
            logger.info(f"Storage created: {storage.id} - {name}")
            return storage
            
        except Exception as e:
            # 发送创建失败通知
            self.notification_service.notify_storage_error(
                user_id=g.user.id,
                storage_name=name,
                error_message=f'创建存储失败: {str(e)}'
            )
            logger.error(f"Failed to create storage {name}: {str(e)}")
            raise
        
    def get_storages(self) -> list[Storage]:
        """获取所有存储节点"""
        return Storage.query.filter_by(user_id=g.user.id).all()
        
    def get_storage(self, storage_id: str) -> Optional[Storage]:
        """获取存储节点详情"""
        return Storage.query.filter_by(id=storage_id, user_id=g.user.id).first()
        
    def update_storage(self, storage_id: str, name: str = None, type: str = None, config: Dict[str, Any] = None, node_id: str = None) -> Optional[Storage]:
        """更新存储节点"""
        storage = Storage.query.filter_by(id=storage_id, user_id=g.user.id).first()
        if not storage:
            return None
        
        try:
            # 记录原始值用于通知
            original_name = storage.name
            original_type = storage.type
            original_node_id = storage.node_id
            
            if type:
                # 验证新的存储类型
                self.get_provider_class(type)
                storage.type = type
                
            if name:
                storage.name = name
            if config:
                storage.config = config
            if node_id is not None:  # 允许设置为None来解绑节点
                storage.node_id = node_id
                
            db.session.commit()
            
            # 发送更新成功通知
            changes = []
            if name and name != original_name:
                changes.append(f'名称: {original_name} → {name}')
            if type and type != original_type:
                changes.append(f'类型: {original_type} → {type}')
            if node_id != original_node_id:
                old_node = original_node_id or '未绑定'
                new_node = node_id or '未绑定'
                changes.append(f'节点: {old_node} → {new_node}')
            
            self._send_storage_notification(
                storage,
                'updated',
                f'存储 {storage.name} 配置已更新',
                {'changes': changes, 'updated_fields': {'name': name, 'type': type, 'node_id': node_id}}
            )
            
            logger.info(f"Storage updated: {storage_id} - {storage.name}")
            return storage
            
        except Exception as e:
            # 发送更新失败通知
            self.notification_service.notify_storage_error(
                user_id=g.user.id,
                storage_name=storage.name,
                error_message=f'更新存储配置失败: {str(e)}'
            )
            logger.error(f"Failed to update storage {storage_id}: {str(e)}")
            raise
        
    def delete_storage(self, storage_id: str) -> bool:
        """删除存储节点"""
        storage = Storage.query.filter_by(id=storage_id, user_id=g.user.id).first()
        if not storage:
            return False
        
        try:
            # 记录存储信息用于日志
            storage_name = storage.name
            storage_type = storage.type
            
            # 检查是否有任务引用此存储
            from backend.app.models.task import Task
            related_tasks = Task.query.filter(
                (Task.source_storage_id == storage_id) | 
                (Task.target_storage_id == storage_id)
            ).all()
            
            if related_tasks:
                # 如果有相关任务，先处理这些任务
                from backend.app.models.task import TaskLog
                
                for task in related_tasks:
                    # 先删除任务相关的日志
                    TaskLog.query.filter_by(task_id=task.id).delete()
                    logger.info(f"Deleted logs for task {task.id}")
                    
                    if task.status in ['running', 'assigned']:
                        # 如果任务正在运行，先取消
                        task.status = 'cancelled'
                        task.error = f'存储 {storage_name} 已删除，任务被取消'
                    elif task.status in ['pending', 'paused']:
                        # 如果任务未运行，直接取消
                        task.status = 'cancelled'
                        task.error = f'存储 {storage_name} 已删除，任务被取消'
                    
                    # 更新存储引用为 None（如果允许的话）
                    if task.source_storage_id == storage_id:
                        task.source_storage_id = None
                    if task.target_storage_id == storage_id:
                        # 目标存储不能为 None，需要特殊处理
                        # 这里我们选择删除这些任务，因为它们无法继续
                        db.session.delete(task)
                        logger.info(f"Deleted task {task.id} due to storage deletion")
                
                # 提交任务更新
                db.session.commit()
                logger.info(f"Processed {len(related_tasks)} related tasks before deleting storage")
            
            # 删除存储
            db.session.delete(storage)
            db.session.commit()
            
            logger.info(f"Storage deleted: {storage_id} - {storage_name}")
            return True
            
        except Exception as e:
            # 回滚事务
            db.session.rollback()
            
            # 发送删除失败通知
            self.notification_service.notify_storage_error(
                user_id=g.user.id,
                storage_name=storage.name,
                error_message=f'删除存储失败: {str(e)}'
            )
            logger.error(f"Failed to delete storage {storage_id}: {str(e)}")
            raise

    def get_provider(self, storage: Storage) -> StorageProvider:
        """获取存储提供者实例"""
        provider_class = self.get_provider_class(storage.type)
        return provider_class(storage.config)

    def create_storage_operation_task(self, storage: Storage, operation: str, params: Dict[str, Any] = None) -> str:
        """创建存储操作任务
        
        Args:
            storage: 存储对象
            operation: 操作类型 (get_stats, list_buckets, list_objects, download_object, etc.)
            params: 操作参数
            
        Returns:
            str: 任务ID
        """
        task_service = TaskService()
        
        # 构建任务数据
        task_data = {
            'name': f"存储操作 - {storage.name} - {operation}",
            'description': f"执行存储操作: {operation}",
            'type': 'storage-operation',
            'priority': 2,  # 中等优先级
            'user_id': g.user.id,
            'source_type': 'storage',
            'options': {
                'storage_config': {
                    'id': storage.id,
                    'name': storage.name,
                    'type': storage.type,
                    'config': storage.config
                },
                'operation': operation,
                'params': params or {}
            }
        }
        
        # 创建任务
        task = task_service.create_task(task_data)
        
        # 启动任务并分配给绑定的节点
        if storage.node_id:
            started_task = task_service.start_task(task.id, storage.node_id)
            return started_task.id
        else:
            raise ValueError("存储未绑定节点，无法执行操作")
   
    def _send_storage_notification(self, storage, operation_type, message, details=None):
        """发送存储操作通知"""
        try:
            if operation_type == 'created':
                self.notification_service.notify_storage_created(
                    user_id=storage.user_id,
                    storage_name=storage.name,
                    storage_type=storage.type
                )
            elif operation_type == 'updated':
                self.notification_service.create_notification(
                    user_id=storage.user_id,
                    type='storage_updated',
                    title=f'存储配置更新: {storage.name}',
                    content=f'{message}\n变更详情: {", ".join(details.get("changes", []))}',
                    level='info'
                )
            elif operation_type == 'connected':
                self.notification_service.notify_storage_connected(
                    user_id=storage.user_id,
                    storage_name=storage.name,
                    storage_type=storage.type
                )
            elif operation_type == 'disconnected':
                self.notification_service.notify_storage_disconnected(
                    user_id=storage.user_id,
                    storage_name=storage.name,
                    reason=details.get('reason', '未知原因')
                )
                
        except Exception as e:
            logger.error(f"发送存储通知失败: {str(e)}")
    
    def monitor_storage_usage(self, storage_id: str, threshold: float = 85.0):
        """监控存储使用率并发送警告"""
        storage = self.get_storage(storage_id)
        if not storage:
            return
        
        try:
            provider = self.get_provider(storage)
            stats = provider.get_stats()
            
            # 检查使用率
            if 'usage_percent' in stats and stats['usage_percent'] > threshold:
                used_space = stats.get('used_space', 0)
                total_space = stats.get('total_space', 0)
                
                self.notification_service.notify_storage_quota_warning(
                    user_id=storage.user_id,
                    storage_name=storage.name,
                    used_space=used_space,
                    total_space=total_space
                )
                
        except Exception as e:
            logger.error(f"监控存储使用率失败: {storage_id} - {str(e)}")
    
    def handle_storage_operation_result(self, storage, operation, result):
        """处理存储操作结果并发送相应通知"""
        try:
            if result.get('status') == 'success':
                # 操作成功通知
                self.notification_service.create_notification(
                    user_id=storage.user_id,
                    type=f'storage_{operation}_success',
                    title=f'存储操作成功: {storage.name}',
                    content=f'操作 "{operation}" 已成功完成。\n结果: {result.get("message", "操作成功")}',
                    level='success'
                )
            else:
                # 操作失败通知
                self.notification_service.notify_storage_error(
                    user_id=storage.user_id,
                    storage_name=storage.name,
                    error_message=f'操作 "{operation}" 失败: {result.get("message", "未知错误")}'
                )
                
        except Exception as e:
            logger.error(f"处理存储操作结果通知失败: {str(e)}")