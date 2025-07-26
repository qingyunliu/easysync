import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from .base import StorageProvider

class NASProvider(StorageProvider):
    """NAS 存储提供者实现"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        # 修正配置字段映射
        self.mount_point = config.get('path', '')
        self.server = config.get('server', '')
        # 协议类型映射：cifs -> smb
        protocol = config.get('protocol', 'smb')
        self.protocol = 'smb' if protocol.lower() == 'cifs' else protocol
        self.workgroup = config.get('workgroup', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.share_path = config.get('path', '')  # 前端发送的是 path，映射到 share_path

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        # 这个方法现在由 Proxy 节点执行，本地不再需要实现
        return {
            "status": "success",
            "message": "存储统计信息获取成功",
            "data": {
                "total_size": 0,
                "used_size": 0,
                "free_size": 0
            }
        }

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

    def list_objects(self, bucket: str, prefix: str = '') -> List[Dict[str, Any]]:
        """列出对象"""
        try:
            # 构建完整路径
            full_path = os.path.join(self.mount_point, prefix)
            if not os.path.exists(full_path):
                raise ValueError(f"路径 {prefix} 不存在")

            # 获取所有对象
            objects = []
            
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
            
            return objects
            
        except Exception as e:
            raise ValueError(f"获取文件列表失败: {str(e)}")

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """上传文件"""
        try:
            # 构建目标路径
            target_path = os.path.join(self.mount_point, object_name)
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, target_path)
            
            return True
        except Exception as e:
            raise ValueError(f"上传文件失败: {str(e)}")

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """下载文件"""
        try:
            # 构建源路径
            source_path = os.path.join(self.mount_point, object_name)
            
            if not os.path.exists(source_path):
                raise ValueError(f"文件 {object_name} 不存在")
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(source_path, file_path)
            
            return True
        except Exception as e:
            raise ValueError(f"下载文件失败: {str(e)}")

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """删除文件"""
        try:
            # 构建文件路径
            file_path = os.path.join(self.mount_point, object_name)
            
            if not os.path.exists(file_path):
                raise ValueError(f"文件 {object_name} 不存在")
            
            # 删除文件
            os.remove(file_path)
            
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
