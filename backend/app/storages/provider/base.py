from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class StorageProvider(ABC):
    """存储提供者基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client = None
        
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """测试连接并获取存储信息"""
        pass
        
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        pass
        
    @abstractmethod
    def list_buckets(self) -> List[Dict[str, Any]]:
        """获取存储桶列表"""
        pass
        
    @abstractmethod
    def list_objects(self, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取对象列表"""
        pass
        
    @abstractmethod
    def download_object(self, bucket: str, key: str) -> bytes:
        """下载对象"""
        pass
        
    @abstractmethod
    def upload_object(self, bucket: str, key: str, data: bytes) -> Dict[str, Any]:
        """上传对象"""
        pass
        
    @abstractmethod
    def delete_object(self, bucket: str, key: str) -> bool:
        """删除对象"""
        pass 