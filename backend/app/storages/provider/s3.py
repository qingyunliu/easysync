from minio import Minio
from minio.error import MinioException, S3Error
from minio.deleteobjects import DeleteObject
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base import StorageProvider

class S3Provider(StorageProvider):
    """S3 兼容的存储提供者实现"""

    @property
    def client(self):
        """获取或创建 MinIO 客户端"""
        if self._client is None:
            endpoint = self.config['endpoint']
            if not endpoint.startswith(('http://', 'https://')):
                endpoint = f"https://{endpoint}"
            endpoint = endpoint.rstrip('/')
            
            # 从endpoint中提取主机名
            from urllib.parse import urlparse
            parsed = urlparse(endpoint)
            host = parsed.netloc
            
            self._client = Minio(
                host,
                access_key=self.config['access_key'],
                secret_key=self.config['secret_key'],
                secure=parsed.scheme == 'https',
                region=self.config.get('region', '')
            )
        
        return self._client

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        # 这个方法现在由 Proxy 节点执行，本地不再需要实现
        return {
            "status": "success",
            "message": "存储统计信息获取成功",
            "data": {
                "bucket_count": 0,
                "object_count": 0,
                "total_size": 0
            }
        }

    def list_buckets(self) -> List[Dict[str, Any]]:
        """获取存储桶列表"""
        try:
            buckets = self.client.list_buckets()
            ret = []
            for obj in (buckets or []):
                created_at = obj.creation_date
                if isinstance(created_at, datetime):
                    created_at = created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                ret.append(
                    {
                        "name": obj.name,
                        "created_at": created_at,
                        "region": self.config.get('region', '')  # 使用配置中的region
                    }
                )
                
            return ret

        except MinioException as e:
            raise ValueError(f"获取存储桶列表失败: {str(e)}")

    def list_objects(self, bucket: str, prefix: str = '') -> List[Dict[str, Any]]:
        """列出对象"""
        try:
            objects = []
            for obj in self.client.list_objects(bucket, prefix=prefix, recursive=False):
                objects.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'modified_time': obj.last_modified.isoformat(),
                    'type': 'file'
                })
            return objects
        except MinioException as e:
            raise ValueError(f"获取对象列表失败: {str(e)}")

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """上传文件"""
        try:
            self.client.fput_object(bucket, object_name, file_path)
            return True
        except MinioException as e:
            raise ValueError(f"上传文件失败: {str(e)}")

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """下载文件"""
        try:
            self.client.fget_object(bucket, object_name, file_path)
            return True
        except MinioException as e:
            raise ValueError(f"下载文件失败: {str(e)}")

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(bucket, object_name)
            return True
        except MinioException as e:
            raise ValueError(f"删除文件失败: {str(e)}") 