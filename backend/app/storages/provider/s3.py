from minio import Minio
from minio.error import MinioException, S3Error
from minio.deleteobjects import DeleteObject
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base import StorageProvider

class S3Provider(StorageProvider):
    """S3 兼容的存储提供者实现"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None

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

    def test_connection(self) -> Dict[str, Any]:
        """测试连接并获取存储信息"""
        try:
            buckets = self.client.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            result = {
                "status": "success",
                "message": "连接成功",
                "data": {
                    "buckets": bucket_names
                }
            }

            if self.config.get('bucket'):
                bucket_name = self.config['bucket']
                try:
                    # 检查存储桶是否存在
                    if not self.client.bucket_exists(bucket_name):
                        result["data"]["current_bucket"] = {
                            "name": bucket_name,
                            "error": f"存储桶 {bucket_name} 不存在"
                        }
                    else:
                        # 获取存储桶中的对象
                        objects = list(self.client.list_objects(
                            bucket_name,
                            recursive=False,
                            max_keys=10
                        ))
                        
                        result["data"]["current_bucket"] = {
                            "name": bucket_name,
                            "region": self.config.get('region', ''),
                            "object_count": len(objects),
                            "objects": [
                                {
                                    "key": obj.object_name,
                                    "size": obj.size,
                                    "last_modified": obj.last_modified.isoformat()
                                }
                                for obj in objects
                            ]
                        }
                except MinioException as e:
                    result["data"]["current_bucket"] = {
                        "name": bucket_name,
                        "error": f"访问存储桶失败: {str(e)}"
                    }

            return result
            
        except MinioException as e:
            raise ValueError(f"连接测试失败: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            buckets = self.client.list_buckets()
            
            stats = {
                "bucket_count": len(buckets),
                "object_count": 0,
                "total_size": 0,
                "last_modified": None,
                "bucket_stats": []
            }
            
            for bucket in buckets:
                bucket_name = bucket.name
                try:
                    size = 0
                    object_count = 0
                    last_modified = None
                    
                    objects = self.client.list_objects(bucket_name, recursive=True)
                    for obj in objects:
                        size += obj.size
                        object_count += 1
                        if not last_modified or obj.last_modified > last_modified:
                            last_modified = obj.last_modified
                    
                    stats["object_count"] += object_count
                    stats["total_size"] += size
                    if not stats["last_modified"] or (last_modified and last_modified > stats["last_modified"]):
                        stats["last_modified"] = last_modified
                    
                    stats["bucket_stats"].append({
                        "name": bucket_name,
                        "region": self.config.get('region', ''),
                        "object_count": object_count,
                        "size": size,
                        "last_modified": last_modified
                    })
                    
                except MinioException:
                    continue
            
            return stats
            
        except MinioException as e:
            raise ValueError(f"获取统计信息失败: {str(e)}")

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

    def list_objects(self, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取对象列表"""
        try:
            # 获取所有对象
            objects = list(self.client.list_objects(
                bucket,
                prefix=prefix,
                recursive=False
            ))
            
            # 计算分页
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_objects = objects[start_idx:end_idx]
            total = len(objects)

            # 处理目录和文件
            directories = []
            files = []
            
            for obj in page_objects:
                if obj.is_dir:
                    name = obj.object_name[len(prefix):].rstrip('/')
                    directories.append({
                        'name': name,
                        'prefix': obj.object_name,
                        'type': 'directory'
                    })
                else:
                    name = obj.object_name[len(prefix):] if prefix else obj.object_name
                    if not name:
                        continue
                    files.append({
                        'name': name,
                        'key': obj.object_name,
                        'size': obj.size,
                        'lastModified': obj.last_modified.isoformat(),
                        'type': 'file'
                    })

            return {
                'objects': directories + files,
                'total': total,
                'page': page,
                'page_size': page_size
            }
            
        except MinioException as e:
            raise ValueError(f"获取对象列表失败: {str(e)}")

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """上传文件"""
        try:
            self.client.fput_object(bucket, object_name, file_path)
            return True
        except MinioException as e:
            raise ValueError(f"上传文件失败: {str(e)}")
    
    def upload_file_to_memory(self, bucket: str, object_name: str, file_data: bytes) -> Dict[str, Any]:
        """上传文件到内存"""
        try:
            result = self.client.put_object(bucket, object_name, file_data, length=len(file_data))
            return {
                "status": "success",
                "message": "上传成功",
                "etag": result.etag
            }
        except MinioException as e:
            raise ValueError(f"上传文件失败: {str(e)}")

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """下载文件"""
        try:
            self.client.fget_object(bucket, object_name, file_path)
            return True
        except MinioException as e:
            raise ValueError(f"下载文件失败: {str(e)}")
    
    def download_file_to_memory(self, bucket: str, object_name: str) -> bytes:
        """下载文件到内存"""
        try:
            return self.client.get_object(bucket, object_name)
        except MinioException as e:
            raise ValueError(f"下载文件失败: {str(e)}")

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(bucket, object_name)
            return True
        except MinioException as e:
            raise ValueError(f"删除文件失败: {str(e)}") 