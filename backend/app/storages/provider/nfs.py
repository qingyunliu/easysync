import os
import shutil
from datetime import datetime
from typing import Dict, Any, List
from .base import StorageProvider

class NFSProvider(StorageProvider):
    """NFS 存储提供者实现"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mount_point = config.get('path', '')
        self.server = config.get('server', '')
        self.version = config.get('version', '4')
        self.options = config.get('options', 'vers=4')

    def test_connection(self) -> Dict[str, Any]:
        """测试连接并获取存储信息"""
        try:
            if not os.path.exists(self.mount_point):
                raise ValueError(f"挂载点 {self.mount_point} 不存在")

            # 获取存储信息
            total, used, free = shutil.disk_usage(self.mount_point)
            
            return {
                "status": "success",
                "message": "连接成功",
                "data": {
                    "total_size": total,
                    "used_size": used,
                    "free_size": free,
                    "mount_point": self.mount_point,
                    "server": self.server,
                    "version": self.version
                }
            }
        except Exception as e:
            raise ValueError(f"连接测试失败: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            total, used, free = shutil.disk_usage(self.mount_point)
            
            # 获取目录统计信息
            total_files = 0
            total_size = 0
            last_modified = None
            
            for root, dirs, files in os.walk(self.mount_point):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        total_files += 1
                        total_size += stat.st_size
                        if not last_modified or stat.st_mtime > last_modified:
                            last_modified = stat.st_mtime
                    except:
                        continue
            
            return {
                "total_size": total,
                "used_size": used,
                "free_size": free,
                "total_files": total_files,
                "total_objects": total_files,
                "last_modified": datetime.fromtimestamp(last_modified).isoformat() if last_modified else None
            }
        except Exception as e:
            raise ValueError(f"获取统计信息失败: {str(e)}")

    def list_buckets(self) -> List[Dict[str, Any]]:
        """获取目录列表（模拟存储桶）"""
        try:
            buckets = []
            for item in os.listdir(self.mount_point):
                item_path = os.path.join(self.mount_point, item)
                if os.path.isdir(item_path):
                    stat = os.stat(item_path)
                    buckets.append({
                        "name": item,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "region": self.server
                    })
            return buckets
        except Exception as e:
            raise ValueError(f"获取目录列表失败: {str(e)}")

    def list_objects(self, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取文件列表"""
        try:
            # 构建完整路径
            full_path = os.path.join(self.mount_point, prefix)
            if not os.path.exists(full_path):
                raise ValueError(f"路径 {prefix} 不存在")

            # 获取所有对象
            objects = []
            total = 0
            
            # 获取当前目录下的文件和文件夹
            try:
                items = os.listdir(full_path)
            except PermissionError:
                raise ValueError(f"没有权限访问路径 {prefix}")
            
            for item in items:
                item_path = os.path.join(full_path, item)
                rel_path = os.path.join(prefix, item) if prefix else item
                
                try:
                    stat = os.stat(item_path)
                    total += 1
                    
                    if total > (page - 1) * page_size and len(objects) < page_size:
                        if os.path.isdir(item_path):
                            objects.append({
                                'name': item,
                                'path': rel_path,
                                'type': 'directory',
                                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
                        else:
                            objects.append({
                                'name': item,
                                'path': rel_path,
                                'size': stat.st_size,
                                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'type': 'file'
                            })
                except (OSError, PermissionError):
                    continue

            return {
                'files': objects,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            raise ValueError(f"获取文件列表失败: {str(e)}")

    def download_object(self, bucket: str, key: str) -> bytes:
        """下载文件"""
        try:
            file_path = os.path.join(self.mount_point, key)
            if not os.path.exists(file_path):
                raise ValueError(f"文件 {key} 不存在")
            
            if not os.path.isfile(file_path):
                raise ValueError(f"{key} 不是一个文件")
            
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"下载文件失败: {str(e)}")

    def upload_object(self, bucket: str, key: str, data: bytes) -> Dict[str, Any]:
        """上传文件"""
        try:
            file_path = os.path.join(self.mount_point, key)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(data)
            
            return {
                'key': key,
                'size': len(data),
                'uploaded_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ValueError(f"上传文件失败: {str(e)}")

    def delete_object(self, bucket: str, key: str) -> bool:
        """删除文件"""
        try:
            file_path = os.path.join(self.mount_point, key)
            if not os.path.exists(file_path):
                return False
            
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                import shutil
                shutil.rmtree(file_path)
            
            return True
        except Exception as e:
            raise ValueError(f"删除文件失败: {str(e)}")

    def mount_check(self) -> dict:
        """检测挂载点是否存在、是否可读写"""
        result = {
            'mount_point': self.mount_point,
            'exists': False,
            'readable': False,
            'writable': False,
            'message': ''
        }
        try:
            if os.path.exists(self.mount_point):
                result['exists'] = True
                # 检查可读
                result['readable'] = os.access(self.mount_point, os.R_OK)
                # 检查可写
                result['writable'] = os.access(self.mount_point, os.W_OK)
                result['message'] = '挂载点存在'
            else:
                result['message'] = '挂载点不存在'
        except Exception as e:
            result['message'] = f'检测异常: {str(e)}'
        return result 