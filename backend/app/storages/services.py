from typing import Dict, Any, List, Type, Optional
from backend.app.models.storage import Storage
from backend.app.storages.provider.base import StorageProvider
from backend.app.storages.provider.nas import NASProvider
from backend.app.storages.provider.s3 import S3Provider
from backend import db
from flask import g
from backend.app.tasks.service import TaskService

class StorageService:
    """存储服务类"""
    
    PROVIDER_MAP = {
        'nas': NASProvider,
        's3': S3Provider,
        'obs': S3Provider  # OBS 使用 S3 提供者
    }
    
    def get_provider_class(self, storage_type: str) -> Type[StorageProvider]:
        """获取存储提供者类"""
        if storage_type not in self.PROVIDER_MAP:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        return self.PROVIDER_MAP[storage_type]
    
    def create_storage(self, name: str, type: str, config: Dict[str, Any]) -> Storage:
        """创建存储节点"""
        # 验证存储类型
        self.get_provider_class(type)
        
        storage = Storage(
            name=name,
            type=type,
            config=config,
            user_id=g.user.id
        )
        db.session.add(storage)
        db.session.commit()
        return storage
        
    def get_storages(self) -> list[Storage]:
        """获取所有存储节点"""
        return Storage.query.filter_by(user_id=g.user.id).all()
        
    def get_storage(self, storage_id: str) -> Optional[Storage]:
        """获取存储节点详情"""
        return Storage.query.filter_by(id=storage_id, user_id=g.user.id).first()
        
    def update_storage(self, storage_id: str, name: str = None, type: str = None, config: Dict[str, Any] = None) -> Optional[Storage]:
        """更新存储节点"""
        storage = Storage.query.filter_by(id=storage_id, user_id=g.user.id).first()
        if not storage:
            return None
            
        if type:
            # 验证新的存储类型
            self.get_provider_class(type)
            storage.type = type
            
        if name:
            storage.name = name
        if config:
            storage.config = config
            
        db.session.commit()
        return storage
        
    def delete_storage(self, storage_id: str) -> bool:
        """删除存储节点"""
        storage = Storage.query.filter_by(id=storage_id, user_id=g.user.id).first()
        if not storage:
            return False
            
        db.session.delete(storage)
        db.session.commit()
        return True

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

    def get_stats(self, storage: Storage, use_task: bool = False) -> Dict[str, Any]:
        """获取存储统计信息"""
        if use_task:
            # 通过任务系统执行
            task_id = self.create_storage_operation_task(storage, 'get_stats')
            return {
                'status': 'task_created',
                'task_id': task_id,
                'message': '统计信息获取任务已创建，请通过任务系统查看结果'
            }
        else:
            # 直接执行（实时模式）
            try:
                provider = self.get_provider(storage)
                stats = provider.get_stats()
                return {
                    'status': 'success',
                    'data': stats
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'获取统计信息失败: {str(e)}'
                }

    def list_buckets(self, storage: Storage, page: int = 1, page_size: int = 20, use_task: bool = False) -> Dict[str, Any]:
        """获取存储桶列表"""
        if use_task:
            # 通过任务系统执行
            params = {'page': page, 'page_size': page_size}
            task_id = self.create_storage_operation_task(storage, 'list_buckets', params)
            return {
                'status': 'task_created',
                'task_id': task_id,
                'message': '存储桶列表获取任务已创建，请通过任务系统查看结果'
            }
        else:
            # 直接执行（实时模式）
            try:
                provider = self.get_provider(storage)
                all_buckets = provider.list_buckets()
                total = len(all_buckets)
                start = (page - 1) * page_size
                end = start + page_size
                return {
                    'status': 'success',
                    'data': {
                        'buckets': all_buckets[start:end],
                        'total': total,
                        'page': page,
                        'page_size': page_size
                    }
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'获取存储桶列表失败: {str(e)}'
                }

    def list_objects(self, storage: Storage, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20, use_task: bool = False) -> Dict[str, Any]:
        """获取对象列表"""
        if use_task:
            # 通过任务系统执行
            params = {
                'bucket': bucket,
                'prefix': prefix,
                'page': page,
                'page_size': page_size
            }
            task_id = self.create_storage_operation_task(storage, 'list_objects', params)
            return {
                'status': 'task_created',
                'task_id': task_id,
                'message': '对象列表获取任务已创建，请通过任务系统查看结果'
            }
        else:
            # 直接执行（实时模式）
            try:
                provider = self.get_provider(storage)
                result = provider.list_objects(bucket, prefix)
                return {
                    'status': 'success',
                    'data': result
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'获取对象列表失败: {str(e)}'
                }

    def download_object(self, storage: Storage, bucket: str, key: str, use_task: bool = True) -> Dict[str, Any]:
        """下载对象"""
        if use_task:
            # 通过任务系统执行
            params = {'bucket': bucket, 'key': key}
            task_id = self.create_storage_operation_task(storage, 'download_object', params)
            return {
                'status': 'task_created',
                'task_id': task_id,
                'message': '文件下载任务已创建，请通过任务系统查看结果'
            }
        else:
            # 直接执行（实时模式）
            try:
                provider = self.get_provider(storage)
                data = provider.download_file(bucket, key, '/tmp/downloaded_file')
                return {
                    'status': 'success',
                    'data': data
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'下载对象失败: {str(e)}'
                }

    def get_nas_stats(self, storage: Storage, use_task: bool = False) -> Dict[str, Any]:
        """获取 NAS 存储统计信息"""
        if use_task:
            # 通过任务系统执行
            task_id = self.create_storage_operation_task(storage, 'get_nas_stats')
            return {
                'status': 'task_created',
                'task_id': task_id,
                'message': 'NAS 统计信息获取任务已创建，请通过任务系统查看结果'
            }
        else:
            # 直接执行（实时模式）
            try:
                provider = self.get_provider(storage)
                stats = provider.get_stats()
                return {
                    'status': 'success',
                    'data': stats
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'获取 NAS 统计信息失败: {str(e)}'
                }

    def list_nas_files(self, storage: Storage, path: str = '', page: int = 1, page_size: int = 20, use_task: bool = False) -> Dict[str, Any]:
        """获取 NAS 文件列表"""
        if use_task:
            # 通过任务系统执行
            params = {
                'path': path,
                'page': page,
                'page_size': page_size
            }
            task_id = self.create_storage_operation_task(storage, 'list_nas_files', params)
            return {
                'status': 'task_created',
                'task_id': task_id,
                'message': 'NAS 文件列表获取任务已创建，请通过任务系统查看结果'
            }
        else:
            # 直接执行（实时模式）
            try:
                provider = self.get_provider(storage)
                result = provider.list_objects('', path, page, page_size)
                return {
                    'status': 'success',
                    'data': result
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'获取 NAS 文件列表失败: {str(e)}'
                }

    def download_nas_file(self, storage: Storage, path: str, use_task: bool = True) -> Dict[str, Any]:
        """下载 NAS 文件"""
        if use_task:
            # 通过任务系统执行
            params = {'path': path}
            task_id = self.create_storage_operation_task(storage, 'download_nas_file', params)
            return {
                'status': 'task_created',
                'task_id': task_id,
                'message': 'NAS 文件下载任务已创建，请通过任务系统查看结果'
            }
        else:
            # 直接执行（实时模式）
            try:
                provider = self.get_provider(storage)
                data = provider.download_file('', path, '/tmp/downloaded_file')
                return {
                    'status': 'success',
                    'data': data
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'下载 NAS 文件失败: {str(e)}'
                }