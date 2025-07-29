from abc import ABC, abstractmethod
from typing import Dict, Any, List

class StorageProvider(ABC):
    """存储提供者基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        pass
    
    @abstractmethod
    def list_buckets(self) -> List[Dict[str, Any]]:
        """列出存储桶"""
        pass
    
    @abstractmethod
    def list_objects(self, bucket: str, prefix: str = '') -> List[Dict[str, Any]]:
        """列出对象"""
        pass
    
    @abstractmethod
    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """上传文件"""
        pass
    
    @abstractmethod
    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """下载文件"""
        pass
    
    @abstractmethod
    def delete_file(self, bucket: str, object_name: str) -> bool:
        """删除文件"""
        pass 