from backend import db
from backend.app.models import Storage
from flask import g
from typing import Dict, Any, Optional, Type
from .provider.base import StorageProvider
from .provider.s3 import S3Provider
from .provider.nfs import NFSProvider
from .provider.nas import NASProvider

class StorageService:
    """存储服务类"""
    
    PROVIDER_MAP = {
        's3': S3Provider,
        'obs': S3Provider,  # OBS 使用 S3 兼容接口
        'oss': S3Provider,  # OSS 使用 S3 兼容接口
        'nfs': NFSProvider,  # NFS 存储
        'nas': NASProvider,  # NAS 存储
    }
    
    def get_provider_class(self, storage_type: str) -> Type[StorageProvider]:
        """获取存储提供者类"""
        provider_class = self.PROVIDER_MAP.get(storage_type.lower())
        if not provider_class:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        return provider_class

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

    def test_connection(self, storage: Storage) -> Dict[str, Any]:
        """测试存储连接"""
        provider = self.get_provider(storage)
        return provider.test_connection()

    def get_stats(self, storage: Storage) -> Dict[str, Any]:
        """获取存储统计信息"""
        provider = self.get_provider(storage)
        return provider.get_stats()

    def list_buckets(self, storage: Storage, page: int = 1, page_size: int = 20) -> list[Dict[str, Any]]:
        """获取存储桶列表"""
        provider = self.get_provider(storage)
        all_buckets = provider.list_buckets()
        total = len(all_buckets)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            'buckets': all_buckets[start:end],
            'total': total,
            'page': page,
            'page_size': page_size
        }

    def list_objects(self, storage: Storage, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取对象列表"""
        provider = self.get_provider(storage)
        return provider.list_objects(bucket, prefix, page, page_size)

    def download_object(self, storage: Storage, bucket: str, key: str) -> bytes:
        """下载对象"""
        provider = self.get_provider(storage)
        return provider.download_object(bucket, key)

    def upload_object(self, storage: Storage, bucket: str, key: str, data: bytes) -> Dict[str, Any]:
        """上传对象"""
        provider = self.get_provider(storage)
        return provider.upload_object(bucket, key, data)

    def delete_object(self, storage: Storage, bucket: str, key: str) -> bool:
        """删除对象"""
        provider = self.get_provider(storage)
        return provider.delete_object(bucket, key)

    def get_nas_stats(self, storage: Storage) -> Dict[str, Any]:
        """获取 NAS 存储统计信息"""
        provider = self.get_provider(storage)
        return provider.get_stats()

    def list_nas_files(self, storage: Storage, path: str = '', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取 NAS 文件列表"""
        provider = self.get_provider(storage)
        return provider.list_objects('', path, page, page_size)

    def download_nas_file(self, storage: Storage, path: str) -> bytes:
        """下载 NAS 文件"""
        provider = self.get_provider(storage)
        return provider.download_object('', path)

    def mount_check(self, storage: Storage) -> dict:
        """检测 NAS/NFS 挂载状态"""
        provider = self.get_provider(storage)
        return provider.mount_check()