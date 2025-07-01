import os
import json
import logging
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from .progress import ProgressMonitor
from ..utils.retry import RetryHandler

class StorageManager:
    """存储管理类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('StorageManager')
        self.mounts = {}  # 存储当前挂载点信息
        self.rclone_configs = {}  # 存储临时的rclone配置
        self.retry_handler = RetryHandler(
            max_retries=config.get('retry', {}).get('max_retries', 3),
            delay=config.get('retry', {}).get('delay', 1.0),
            backoff=config.get('retry', {}).get('backoff', 2.0)
        )
        
    def _create_rclone_config(self, storage_config: Dict[str, Any]) -> str:
        """创建临时的rclone配置
        
        Args:
            storage_config: 存储配置信息
                {
                    'type': 'obs',
                    'provider': 'AWS' | 'ALIYUN' | 'HUAWEI',
                    'access_key': 'YOUR_ACCESS_KEY',
                    'secret_key': 'YOUR_SECRET_KEY',
                    'region': 'region',
                    'endpoint': 'endpoint',
                    'bucket': 'bucket',
                    'path': 'path'
                }
                
        Returns:
            str: 临时配置文件路径
        """
        try:
            # 创建临时配置文件
            fd, config_path = tempfile.mkstemp(suffix='.conf')
            os.close(fd)
            
            # 生成rclone配置
            rclone_config = {
                "remotes": {
                    "temp": {
                        "type": "s3",
                        "provider": storage_config['provider'],
                        "access_key_id": storage_config['access_key'],
                        "secret_access_key": storage_config['secret_key'],
                        "region": storage_config['region'],
                        "endpoint": storage_config['endpoint'],
                        "acl": "private",
                        "storage_class": "STANDARD"
                    }
                }
            }
            
            # 写入配置文件
            with open(config_path, 'w') as f:
                json.dump(rclone_config, f, indent=4)
                
            return config_path
            
        except Exception as e:
            self.logger.error(f"Error creating rclone config: {e}")
            raise
            
    @RetryHandler.retry
    def mount(self, storage_config: Dict[str, Any]) -> str:
        """挂载存储（仅用于NFS/NAS）
        
        Args:
            storage_config: 存储配置信息
                {
                    'type': 'nfs',
                    'source': 'nfs://server/path',
                    'mount_point': '/mnt/point',
                    'options': {
                        'username': 'user',
                        'password': 'pass',
                        'vers': '4',
                        'timeo': '600',
                        'retrans': '2'
                    }
                }
                
        Returns:
            str: 挂载点路径
        """
        try:
            storage_type = storage_config['type']
            if storage_type != 'nfs':
                raise ValueError(f"Only NFS/NAS storage can be mounted: {storage_type}")
                
            source = storage_config['source']
            mount_point = storage_config['mount_point']
            options = storage_config.get('options', {})
            
            # 确保挂载点存在
            os.makedirs(mount_point, exist_ok=True)
            
            # 执行NFS挂载
            self._mount_nfs(source, mount_point, options)
            
            # 记录挂载信息
            self.mounts[mount_point] = {
                'type': storage_type,
                'source': source,
                'options': options,
                'mounted_at': datetime.utcnow().isoformat()
            }
            
            return mount_point
            
        except Exception as e:
            self.logger.error(f"Error mounting storage: {e}")
            raise
            
    @RetryHandler.retry
    def unmount(self, mount_point: str) -> bool:
        """卸载存储
        
        Args:
            mount_point: 挂载点路径
            
        Returns:
            bool: 是否成功卸载
        """
        try:
            if mount_point not in self.mounts:
                raise ValueError(f"Mount point not found: {mount_point}")
                
            # 执行卸载命令
            subprocess.run(['umount', mount_point], check=True)
            
            # 删除挂载点
            os.rmdir(mount_point)
            
            # 移除挂载记录
            del self.mounts[mount_point]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unmounting storage: {e}")
            raise
            
    def _mount_nfs(self, source: str, mount_point: str, options: Dict[str, Any]):
        """挂载NFS/NAS"""
        try:
            # 构建挂载命令
            cmd = ['mount', '-t', 'nfs']
            
            # 添加选项
            if options:
                opts = []
                # 基本选项
                if 'username' in options:
                    opts.append(f"username={options['username']}")
                if 'password' in options:
                    opts.append(f"password={options['password']}")
                    
                # NFS特定选项
                if 'vers' in options:
                    opts.append(f"vers={options['vers']}")
                if 'timeo' in options:
                    opts.append(f"timeo={options['timeo']}")
                if 'retrans' in options:
                    opts.append(f"retrans={options['retrans']}")
                    
                if opts:
                    cmd.extend(['-o', ','.join(opts)])
                    
            # 添加源和目标
            cmd.extend([source, mount_point])
            
            # 执行挂载
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            self.logger.error(f"Error mounting NFS/NAS: {e}")
            raise
    
    def check_storage(self, storage_config: Dict[str, Any]) -> bool:
        """检查存储配置"""
        try:
            storage_type = storage_config['type']
            if storage_type == 'nfs':
                return self._check_nfs(storage_config)
            elif storage_type == 'obs':
                return self._check_obs(storage_config)
            else:
                raise ValueError(f"Unsupported storage type: {storage_type}")
                
        except Exception as e:
            self.logger.error(f"Error checking storage: {e}")
            return False
    
    def _check_nfs(self, storage_config: Dict[str, Any]) -> bool:
        """检查NFS/NAS配置"""
        try:
            # 检查挂载点是否存在
            mount_point = storage_config['mount_point']
            if not os.path.exists(mount_point):
                return False
            
            # 检查挂载点是否已挂载
            if mount_point in self.mounts:
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking NFS/NAS: {e}")
            return False
    
    def _check_obs(self, storage_config: Dict[str, Any]) -> bool:
        """检查OBS是否可以访问"""
        try:
            # 检查OBS配置
            provider = storage_config['provider']
            access_key = storage_config['access_key']
            secret_key = storage_config['secret_key']
            region = storage_config['region']
            endpoint = storage_config['endpoint']
            bucket = storage_config['bucket']
            path = storage_config['path']
            
            # 使用rclone检查OBS配置
            rclone_config = self._create_rclone_config(storage_config)
            
            # 执行rclone ls命令
            cmd = ['rclone', '--config', rclone_config, 'ls', f"temp:{bucket}/{path}"]
            subprocess.run(cmd, check=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking OBS: {e}")
            return False
    
    def sync_data(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                 options: Dict[str, Any] = None, progress_callback: Optional[Callable] = None) -> bool:
        """同步数据"""
        try:
            source_type = source_config['type']
            target_type = target_config['type']
            
            # 创建进度监控器
            monitor = ProgressMonitor(progress_callback)
            monitor.start()
            
            # 根据不同的存储类型组合选择同步方式
            if source_type == 'nfs' and target_type == 'obs':
                return self._sync_nfs_to_obs(source_config, target_config, options, monitor)
            elif source_type == 'nfs' and target_type == 'nfs':
                return self._sync_nfs_to_nfs(source_config, target_config, options, monitor)
            elif source_type == 'obs' and target_type == 'obs':
                return self._sync_obs_to_obs(source_config, target_config, options, monitor)
            elif source_type == 'obs' and target_type == 'nfs':
                return self._sync_obs_to_nfs(source_config, target_config, options, monitor)
            else:
                raise ValueError(f"Unsupported sync combination: {source_type} -> {target_type}")
                
        except Exception as e:
            self.logger.error(f"Error syncing data: {e}")
            raise
            
    def _sync_nfs_to_obs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                        options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """NFS/NAS -> OBS 同步"""
        try:
            # 挂载NFS
            source_mount = self.mount(source_config)
            
            # 创建临时的rclone配置
            rclone_config = self._create_rclone_config(target_config)
            
            try:
                # 使用rclone同步到OBS
                cmd = ['rclone', '--config', rclone_config, 'sync']
                
                # 添加选项
                if options:
                    for key, value in options.items():
                        cmd.extend([f'--{key}', str(value)])
                        
                # 添加源和目标
                cmd.extend([source_mount, f"temp:{target_config['bucket']}/{target_config['path']}"])
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # 监控进度
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                # 清理资源
                self.unmount(source_mount)
                os.unlink(rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in NFS/NAS to OBS sync: {e}")
            raise
            
    def _sync_nfs_to_nfs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                         options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """NFS/NAS -> NFS/NAS 同步"""
        try:
            # 挂载源NFS
            source_mount = self.mount(source_config)
            
            # 挂载目标NFS
            target_mount = self.mount(target_config)
            
            try:
                # 使用rsync同步
                cmd = ['rsync', '-avz']
                
                # 添加选项
                if options:
                    if options.get('delete'):
                        cmd.append('--delete')
                    if options.get('exclude'):
                        for pattern in options['exclude']:
                            cmd.extend(['--exclude', pattern])
                    if options.get('include'):
                        for pattern in options['include']:
                            cmd.extend(['--include', pattern])
                            
                # 添加源和目标
                cmd.extend([source_mount, target_mount])
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # 监控进度
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rsync_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                # 卸载存储
                self.unmount(source_mount)
                self.unmount(target_mount)
                
        except Exception as e:
            self.logger.error(f"Error in NFS/NAS to NFS/NAS sync: {e}")
            raise
            
    def _sync_obs_to_obs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                        options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """OBS -> OBS 同步"""
        try:
            # 创建临时的rclone配置
            source_rclone_config = self._create_rclone_config(source_config)
            target_rclone_config = self._create_rclone_config(target_config)
            
            try:
                # 使用rclone同步
                cmd = ['rclone', '--config', source_rclone_config, 'sync']
                
                # 添加选项
                if options:
                    for key, value in options.items():
                        cmd.extend([f'--{key}', str(value)])
                        
                # 添加源和目标
                cmd.extend([
                    f"temp:{source_config['bucket']}/{source_config['path']}",
                    f"temp:{target_config['bucket']}/{target_config['path']}"
                ])
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # 监控进度
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                # 清理资源
                os.unlink(source_rclone_config)
                os.unlink(target_rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in OBS to OBS sync: {e}")
            raise
            
    def _sync_obs_to_nfs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                         options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """OBS -> NFS/NAS 同步"""
        try:
            # 挂载NFS
            target_mount = self.mount(target_config)
            
            # 创建临时的rclone配置
            rclone_config = self._create_rclone_config(source_config)
            
            try:
                # 使用rclone同步
                cmd = ['rclone', '--config', rclone_config, 'sync']
                
                # 添加选项
                if options:
                    for key, value in options.items():
                        cmd.extend([f'--{key}', str(value)])
                        
                # 添加源和目标
                cmd.extend([f"temp:{source_config['bucket']}/{source_config['path']}", target_mount])
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # 监控进度
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                # 清理资源
                self.unmount(target_mount)
                os.unlink(rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in OBS to NFS/NAS sync: {e}")
            raise
            
    def list_mounts(self) -> Dict[str, Dict[str, Any]]:
        """列出所有挂载点"""
        return self.mounts
        
    def get_mount_info(self, mount_point: str) -> Optional[Dict[str, Any]]:
        """获取挂载点信息"""
        return self.mounts.get(mount_point) 