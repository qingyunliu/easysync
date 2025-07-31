# -*- coding: utf-8 -*-
import os
import subprocess
import logging
import time
import threading
from typing import Dict, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MountManager:
    """统一的挂载点管理器"""
    
    def __init__(self):
        self._active_mounts: Dict[str, Dict] = {}  # storage_id -> mount_info
        self._mount_lock = threading.Lock()
        self._base_mount_dir = "/tmp/easysync_mounts"
        self._ensure_base_dir()
        
    def _ensure_base_dir(self):
        """确保基础挂载目录存在"""
        try:
            os.makedirs(self._base_mount_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"创建基础挂载目录失败: {e}")
            
    def get_mount_point(self, storage_id: str) -> str:
        """获取存储的标准挂载点路径"""
        return os.path.join(self._base_mount_dir, f"storage_{storage_id}")
        
    def is_mounted(self, storage_id: str) -> bool:
        """检查存储是否已挂载"""
        mount_point = self.get_mount_point(storage_id)
        
        # 检查挂载点是否在系统挂载表中
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if result.returncode == 0:
                return mount_point in result.stdout
        except Exception as e:
            logger.error(f"检查挂载状态失败: {e}")
            
        # 备用检查：是否是挂载点
        try:
            return os.path.ismount(mount_point)
        except Exception:
            return False
            
    def mount_storage(self, storage_id: str, storage_config: dict) -> Optional[str]:
        """挂载存储，返回挂载点路径"""
        with self._mount_lock:
            # 检查是否已经挂载
            if self.is_mounted(storage_id):
                mount_point = self.get_mount_point(storage_id)
                logger.info(f"存储 {storage_id} 已挂载到 {mount_point}")
                
                # 更新活跃挂载记录
                self._active_mounts[storage_id] = {
                    'mount_point': mount_point,
                    'storage_config': storage_config,
                    'mount_time': datetime.now(),
                    'ref_count': self._active_mounts.get(storage_id, {}).get('ref_count', 0) + 1
                }
                return mount_point
            
            # 执行挂载
            mount_point = self.get_mount_point(storage_id)
            success = self._do_mount(storage_id, storage_config, mount_point)
            
            if success:
                # 记录活跃挂载
                self._active_mounts[storage_id] = {
                    'mount_point': mount_point,
                    'storage_config': storage_config,
                    'mount_time': datetime.now(),
                    'ref_count': 1
                }
                logger.info(f"存储 {storage_id} 成功挂载到 {mount_point}")
                return mount_point
            else:
                logger.error(f"存储 {storage_id} 挂载失败")
                return None
                
    def _do_mount(self, storage_id: str, storage_config: dict, mount_point: str) -> bool:
        """执行实际的挂载操作"""
        try:
            # 确保挂载点目录存在
            os.makedirs(mount_point, exist_ok=True)
            
            storage_type = storage_config.get('type', '').lower()
            
            if storage_type in ['nfs', 'nas']:
                return self._mount_nfs(storage_config, mount_point)
            elif storage_type in ['smb', 'cifs']:
                return self._mount_smb(storage_config, mount_point)
            else:
                logger.error(f"不支持的存储类型: {storage_type}")
                return False
                
        except Exception as e:
            logger.error(f"挂载存储 {storage_id} 时发生异常: {e}")
            return False
            
    def _mount_nfs(self, config: dict, mount_point: str) -> bool:
        """挂载NFS存储"""
        try:
            server = config.get('server') or config.get('host')
            path = config.get('path') or config.get('share_path')
            
            if not server or not path:
                logger.error("NFS配置缺少server或path")
                return False
                
            # 构建NFS挂载命令
            nfs_source = f"{server}:{path}"
            mount_options = config.get('mount_options', 'rw,soft,timeo=30,retry=3')
            
            cmd = ['mount', '-t', 'nfs', '-o', mount_options, nfs_source, mount_point]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"NFS挂载成功: {nfs_source} -> {mount_point}")
                return True
            else:
                logger.error(f"NFS挂载失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("NFS挂载超时")
            return False
        except Exception as e:
            logger.error(f"NFS挂载异常: {e}")
            return False
            
    def _mount_smb(self, config: dict, mount_point: str) -> bool:
        """挂载SMB/CIFS存储"""
        try:
            server = config.get('server') or config.get('host')
            share = config.get('share') or config.get('share_path')
            username = config.get('username', '')
            password = config.get('password', '')
            
            if not server or not share:
                logger.error("SMB配置缺少server或share")
                return False
                
            # 构建SMB挂载命令
            smb_source = f"//{server}/{share}"
            mount_options = ['rw', 'soft']
            
            if username:
                mount_options.append(f"username={username}")
            if password:
                mount_options.append(f"password={password}")
            else:
                mount_options.append("guest")
                
            cmd = ['mount', '-t', 'cifs', '-o', ','.join(mount_options), smb_source, mount_point]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"SMB挂载成功: {smb_source} -> {mount_point}")
                return True
            else:
                logger.error(f"SMB挂载失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("SMB挂载超时")
            return False
        except Exception as e:
            logger.error(f"SMB挂载异常: {e}")
            return False
            
    def unmount_storage(self, storage_id: str) -> bool:
        """卸载存储"""
        with self._mount_lock:
            if storage_id not in self._active_mounts:
                logger.warning(f"存储 {storage_id} 未在活跃挂载记录中")
                # 尝试强制卸载
                mount_point = self.get_mount_point(storage_id)
                return self._do_unmount(mount_point)
                
            mount_info = self._active_mounts[storage_id]
            mount_point = mount_info['mount_point']
            
            # 减少引用计数
            mount_info['ref_count'] = mount_info.get('ref_count', 1) - 1
            
            # 如果还有引用，不卸载
            if mount_info['ref_count'] > 0:
                logger.info(f"存储 {storage_id} 还有 {mount_info['ref_count']} 个引用，暂不卸载")
                return True
                
            # 执行卸载
            success = self._do_unmount(mount_point)
            
            if success:
                # 从活跃挂载记录中移除
                del self._active_mounts[storage_id]
                logger.info(f"存储 {storage_id} 成功卸载")
            else:
                # 卸载失败，恢复引用计数
                mount_info['ref_count'] = 1
                logger.error(f"存储 {storage_id} 卸载失败")
                
            return success
            
    def _do_unmount(self, mount_point: str) -> bool:
        """执行实际的卸载操作"""
        try:
            # 检查是否真的是挂载点
            if not os.path.ismount(mount_point) and not self._is_in_mount_table(mount_point):
                logger.info(f"路径 {mount_point} 不是挂载点，无需卸载")
                # 清理空目录
                try:
                    if os.path.exists(mount_point) and not os.listdir(mount_point):
                        os.rmdir(mount_point)
                except Exception:
                    pass
                return True
                
            # 尝试正常卸载
            result = subprocess.run(['umount', mount_point], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"成功卸载: {mount_point}")
                # 清理空目录
                try:
                    if os.path.exists(mount_point) and not os.listdir(mount_point):
                        os.rmdir(mount_point)
                except Exception:
                    pass
                return True
            else:
                logger.warning(f"正常卸载失败，尝试强制卸载: {result.stderr}")
                # 尝试强制卸载
                result = subprocess.run(['umount', '-f', mount_point], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    logger.info(f"强制卸载成功: {mount_point}")
                    return True
                else:
                    logger.error(f"强制卸载也失败: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            logger.error(f"卸载操作超时: {mount_point}")
            return False
        except Exception as e:
            logger.error(f"卸载异常: {e}")
            return False
            
    def _is_in_mount_table(self, mount_point: str) -> bool:
        """检查挂载点是否在系统挂载表中"""
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if result.returncode == 0:
                return mount_point in result.stdout
        except Exception:
            pass
        return False
        
    def cleanup_abandoned_mounts(self) -> int:
        """清理废弃的挂载点"""
        cleaned_count = 0
        
        try:
            # 扫描基础挂载目录
            if not os.path.exists(self._base_mount_dir):
                return 0
                
            for item in os.listdir(self._base_mount_dir):
                mount_path = os.path.join(self._base_mount_dir, item)
                
                if not os.path.isdir(mount_path):
                    continue
                    
                # 检查是否是已知的活跃挂载
                storage_id = item.replace('storage_', '') if item.startswith('storage_') else None
                
                if storage_id and storage_id in self._active_mounts:
                    continue
                    
                # 尝试卸载废弃的挂载点
                if self._do_unmount(mount_path):
                    cleaned_count += 1
                    logger.info(f"清理废弃挂载点: {mount_path}")
                    
        except Exception as e:
            logger.error(f"清理废弃挂载点时发生异常: {e}")
            
        return cleaned_count
        
    def get_active_mounts(self) -> Dict[str, Dict]:
        """获取活跃挂载列表"""
        with self._mount_lock:
            return self._active_mounts.copy()
            
    def force_unmount_all(self) -> int:
        """强制卸载所有挂载点"""
        unmounted_count = 0
        
        with self._mount_lock:
            storage_ids = list(self._active_mounts.keys())
            
            for storage_id in storage_ids:
                mount_info = self._active_mounts[storage_id]
                mount_point = mount_info['mount_point']
                
                if self._do_unmount(mount_point):
                    del self._active_mounts[storage_id]
                    unmounted_count += 1
                    
        # 清理废弃挂载点
        unmounted_count += self.cleanup_abandoned_mounts()
        
        return unmounted_count

# 全局挂载管理器实例
_mount_manager = None

def get_mount_manager() -> MountManager:
    """获取全局挂载管理器实例"""
    global _mount_manager
    if _mount_manager is None:
        _mount_manager = MountManager()
    return _mount_manager