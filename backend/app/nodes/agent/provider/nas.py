import os
import shutil
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

    def list_buckets(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
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
            
            # 实现分页
            total_count = len(buckets)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            # 确保页码有效
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            
            # 获取当前页的数据
            paginated_buckets = buckets[start_index:end_index]
            
            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size  # 向上取整
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                'buckets': paginated_buckets,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev,
                    'start_index': start_index + 1 if total_count > 0 else 0,
                    'end_index': min(end_index, total_count)
                }
            }
        except Exception as e:
            raise ValueError(f"获取目录列表失败: {str(e)}")

    def list_objects(self, prefix: str = '', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """列出文件"""
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
            total_pages = (total_count + page_size - 1) // page_size  # 向上取整
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
                }
            }
            
        except Exception as e:
            raise ValueError(f"获取文件列表失败: {str(e)}")

    def upload_file(self, file_path: str, target_path: str) -> bool:
        """上传文件"""
        try:
            # 构建目标路径
            target_path = os.path.join(self.mount_point, target_path)
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, target_path)
            
            return True
        except Exception as e:
            raise ValueError(f"上传文件失败: {str(e)}")

    def download_file(self, source_path: str, target_path: str) -> bool:
        """下载文件"""
        try:
            # 构建源路径
            source_path = os.path.join(self.mount_point, source_path)
            
            if not os.path.exists(source_path):
                raise ValueError(f"文件 {source_path} 不存在")
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(source_path, target_path)
            
            return True
        except Exception as e:
            raise ValueError(f"下载文件失败: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            # 构建文件路径
            file_path = os.path.join(self.mount_point, file_path)
            
            if not os.path.exists(file_path):
                raise ValueError(f"文件 {file_path} 不存在")
            
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