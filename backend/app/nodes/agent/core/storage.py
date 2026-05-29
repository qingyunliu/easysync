import os
import json
import re
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple, Callable
from datetime import datetime
from .progress import ProgressMonitor
from ..utils.retry import RetryHandler
from ..utils.logger import get_log_manager
from ..services.mount_manager import get_mount_manager

class StorageManager:
    """存储管理类"""
    
    def __init__(self, config: Dict[str, Any], task_manager = None):
        self.config = config
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('StorageManager')
        self.mount_manager = get_mount_manager()  # 使用统一的挂载管理器
        self.task_manager = task_manager  # 添加任务管理器引用
        self.rclone_configs = {}  # 存储临时的rclone配置
        self.retry_handler = RetryHandler(
            max_retries=config.get('retry', {}).get('max_retries', 3),
            delay=config.get('retry', {}).get('delay', 1.0),
            backoff=config.get('retry', {}).get('backoff', 2.0)
        )
        
        # 初始化存储类型到同步方法的映射
        self.sync_methods = {
            # NFS/NAS 相关
            ('nfs', 'obs'): self._sync_nfs_to_obs,
            ('nfs', 'nfs'): self._sync_nfs_to_nfs,
            ('nfs', 'nas'): self._sync_nfs_to_nfs,
            ('nas', 'nfs'): self._sync_nfs_to_nfs,
            ('nas', 'obs'): self._sync_nfs_to_obs,
            ('nas', 's3'): self._sync_nfs_to_obs,
            ('nas', 'nas'): self._sync_nfs_to_nfs,
            
            # OBS/S3 相关
            ('obs', 'obs'): self._sync_obs_to_obs,
            ('obs', 'nfs'): self._sync_obs_to_nfs,
            ('obs', 'nas'): self._sync_obs_to_nfs,
            ('obs', 's3'): self._sync_obs_to_obs,
            ('s3', 'obs'): self._sync_obs_to_obs,
            ('s3', 'nfs'): self._sync_obs_to_nfs,
            ('s3', 'nas'): self._sync_obs_to_nfs,
            ('s3', 's3'): self._sync_obs_to_obs,
        }
        
        # 初始化存储类型到复制方法的映射
        self.copy_methods = {
            # NFS/NAS 相关
            ('nfs', 'obs'): self._copy_nfs_to_obs,
            ('nfs', 'nfs'): self._copy_nfs_to_nfs,
            ('nfs', 'nas'): self._copy_nfs_to_nfs,
            ('nas', 'nfs'): self._copy_nfs_to_nfs,
            ('nas', 'obs'): self._copy_nfs_to_obs,
            ('nas', 'nas'): self._copy_nfs_to_nfs,
            
            # OBS/S3 相关
            ('obs', 'obs'): self._copy_obs_to_obs,
            ('obs', 'nfs'): self._copy_obs_to_nfs,
            ('obs', 'nas'): self._copy_obs_to_nfs,
            ('s3', 'obs'): self._copy_obs_to_obs,
            ('s3', 'nfs'): self._copy_obs_to_nfs,
            ('s3', 'nas'): self._copy_obs_to_nfs,
        }
        
    def _create_rclone_config(self, storage_config: Dict[str, Any]) -> str:
        """创建临时的rclone配置文件"""
        import tempfile
        import threading
        
        # 为每个线程生成唯一的远程存储名称
        thread_id = threading.get_ident()
        remote_name = f"temp_{thread_id}"
        
        # 处理嵌套的storage_config结构
        if 'config' in storage_config:
            config = storage_config.get('config', {})
        else:
            config = storage_config
        
        # 获取OBS配置
        provider = config.get('provider', 'huawei')
        access_key = config.get('access_key')
        secret_key = config.get('secret_key')
        region = config.get('region', 'cn-north-4')
        endpoint = config.get('endpoint', 'obs.cn-north-4.myhuaweicloud.com')
        bucket = config.get('bucket', '')
        
        # 创建临时配置文件
        config_path = tempfile.mktemp(suffix='.conf')
        
        # 生成INI格式的配置内容
        # 对于华为云OBS，使用Other作为provider
        config_content = f"""[{remote_name}]
type = s3
provider = Other
access_key_id = {access_key}
secret_access_key = {secret_key}
region = {region}
endpoint = {endpoint}
acl = private
storage_class = STANDARD
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
            
        self.logger.debug(f"创建rclone配置文件: {config_path}, 远程存储: {remote_name}")
        self.logger.debug(f"OBS配置 - access_key: {'***' if access_key else 'None'}, secret_key: {'***' if secret_key else 'None'}")
        return config_path, remote_name
    
    def _create_dual_rclone_config(self, source_config: Dict[str, Any], target_config: Dict[str, Any]) -> tuple:
        """创建包含源和目标两个远程存储的rclone配置文件"""
        import tempfile
        import threading
        
        # 为每个线程生成唯一的远程存储名称
        thread_id = threading.get_ident()
        source_remote_name = f"source_{thread_id}"
        target_remote_name = f"target_{thread_id}"
        
        # 处理源配置
        if 'config' in source_config:
            source_config_inner = source_config.get('config', {})
        else:
            source_config_inner = source_config
        
        # 处理目标配置
        if 'config' in target_config:
            target_config_inner = target_config.get('config', {})
        else:
            target_config_inner = target_config
        
        # 获取源OBS配置
        source_access_key = source_config_inner.get('access_key')
        source_secret_key = source_config_inner.get('secret_key')
        source_region = source_config_inner.get('region', 'cn-north-4')
        source_endpoint = source_config_inner.get('endpoint', 'obs.cn-north-4.myhuaweicloud.com')
        source_bucket = source_config_inner.get('bucket', '')

        # 获取目标OBS配置
        target_access_key = target_config_inner.get('access_key')
        target_secret_key = target_config_inner.get('secret_key')
        target_region = target_config_inner.get('region', 'cn-north-4')
        target_endpoint = target_config_inner.get('endpoint', 'obs.cn-north-4.myhuaweicloud.com')
        target_bucket = target_config_inner.get('bucket', '')

        # 处理 endpoint 格式，统一使用 bucket.endpoint 格式
        # 对于S3兼容存储，推荐使用 bucket.endpoint 格式
        if source_bucket and source_endpoint:
            # 检查 endpoint 是否已经包含 bucket 名称
            if not source_endpoint.startswith(source_bucket + '.'):
                source_endpoint = f"{source_bucket}.{source_endpoint}"

        if target_bucket and target_endpoint:
            # 检查 endpoint 是否已经包含 bucket 名称
            if not target_endpoint.startswith(target_bucket + '.'):
                target_endpoint = f"{target_bucket}.{target_endpoint}"

        # 创建临时配置文件
        config_path = tempfile.mktemp(suffix='.conf')

        # 生成INI格式的配置内容，包含两个远程存储
        config_content = f"""[{source_remote_name}]
type = s3
provider = Other
access_key_id = {source_access_key}
secret_access_key = {source_secret_key}
region = {source_region}
endpoint = {source_endpoint}
acl = private
storage_class = STANDARD

[{target_remote_name}]
type = s3
provider = Other
access_key_id = {target_access_key}
secret_access_key = {target_secret_key}
region = {target_region}
endpoint = {target_endpoint}
acl = private
storage_class = STANDARD
"""

        with open(config_path, 'w') as f:
            f.write(config_content)

        self.logger.debug(f"创建双远程存储rclone配置文件: {config_path}")
        self.logger.debug(f"源远程存储: {source_remote_name}, endpoint: {source_endpoint}")
        self.logger.debug(f"目标远程存储: {target_remote_name}, endpoint: {target_endpoint}")
        return config_path, source_remote_name, target_remote_name
            
    def mount(self, storage_config: Dict[str, Any]) -> str:
        """挂载存储
        
        使用统一的挂载管理器
        
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
            # 生成存储ID
            storage_id = self._generate_storage_id(storage_config)
            
            # 使用挂载管理器挂载
            mount_point = self.mount_manager.mount_storage(storage_id, storage_config)
            
            if mount_point:
                self.logger.info(f"成功挂载存储 {storage_id} 到 {mount_point}")
                return mount_point
            else:
                raise Exception(f"挂载存储 {storage_id} 失败")
                
        except Exception as e:
            self.logger.error(f"挂载失败: {e}")
            raise
    
    def _generate_storage_id(self, storage_config: Dict[str, Any]) -> str:
        """生成存储ID"""
        try:
            # 处理存储配置结构
            if 'source' in storage_config:
                # 如果已经有source字段，直接使用
                source = storage_config['source']
            else:
                # 从config字段中提取信息
                config = storage_config.get('config', {})
                server = config.get('server')
                path = config.get('path')
                
                if not server or not path:
                    raise ValueError(f"Missing server or path in storage config: {storage_config}")
                
                # 构建source字符串
                source = f"{server}:{path}"
            
            # 生成唯一的存储ID
            storage_id = storage_config.get('id', str(hash(source) % 10000))
            return storage_id
            
        except Exception as e:
            self.logger.error(f"生成存储ID失败: {e}")
            return str(hash(str(storage_config)) % 10000)
    
    def _get_storage_id_from_mount_point(self, mount_point: str) -> Optional[str]:
        """从挂载点路径反推存储ID"""
        try:
            # 从挂载点路径中提取存储ID
            # 挂载点格式: /tmp/easysync_mounts/storage_{storage_id}
            if '/tmp/easysync_mounts/storage_' in mount_point:
                storage_id = mount_point.split('storage_')[-1]
                return storage_id
            else:
                # 如果格式不匹配，尝试从挂载管理器中查找
                active_mounts = self.mount_manager.get_active_mounts()
                for storage_id, mount_info in active_mounts.items():
                    if mount_info.get('mount_point') == mount_point:
                        return storage_id
                return None
                
        except Exception as e:
            self.logger.error(f"从挂载点反推存储ID失败: {e}")
            return None
            
    def unmount(self, mount_point: str) -> bool:
        """卸载存储
        
        使用统一的挂载管理器
        
        Args:
            mount_point: 挂载点路径
            
        Returns:
            bool: 是否成功卸载
        """
        try:
            # 从挂载点路径反推存储ID
            storage_id = self._get_storage_id_from_mount_point(mount_point)
            
            if storage_id:
                # 使用挂载管理器卸载
                success = self.mount_manager.unmount_storage(storage_id)
                if success:
                    self.logger.info(f"成功卸载存储 {storage_id}")
                    return True
                else:
                    self.logger.error(f"卸载存储 {storage_id} 失败")
                    return False
            else:
                # 如果无法确定存储ID，尝试直接卸载
                self.logger.warning(f"无法确定存储ID，尝试直接卸载: {mount_point}")
                try:
                    subprocess.run(['umount', mount_point], check=True)
                    self.logger.info(f"直接卸载成功: {mount_point}")
                    return True
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"直接卸载失败: {e}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"卸载失败: {e}")
            return False
    
    def check_storage(self, storage_config: Dict[str, Any]) -> bool:
        """检查存储配置是否可用
        
        Args:
            storage_config: 存储配置
            
        Returns:
            bool: 是否可用
        """
        try:
            # 处理存储配置结构
            if 'config' in storage_config:
                # 如果配置在 'config' 字段中，合并配置
                config = storage_config.get('config', {})
                storage_type = storage_config.get('type', config.get('type', 'unknown'))
                # 合并配置，config 中的字段优先级更高
                final_config = {**storage_config, **config}
                final_config['type'] = storage_type
                self.logger.debug(f"合并后的存储配置: {final_config}")
            else:
                final_config = storage_config
                storage_type = storage_config.get('type', 'unknown')
            
            if storage_type == 'nfs' or storage_type == 'nas':
                return self._check_nfs(final_config)
            elif storage_type == 'obs' or storage_type == 's3':
                return self._check_obs(final_config)
            else:
                self.logger.warning(f"不支持的存储类型: {storage_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"检查存储时出错: {e}")
            return False
    
    def _check_nfs(self, storage_config: Dict[str, Any]) -> bool:
        """检查NFS/NAS存储可用性"""
        try:
            # 从嵌套结构中获取配置
            config = storage_config.get('config', {})
            server = config.get('server')
            path = config.get('path')
            
            if not server or not path:
                self.logger.error(f"NFS配置缺少必需字段: server={server}, path={path}")
                return False
            
            # 使用存储ID进行测试挂载
            storage_id = storage_config.get('id')
            if not storage_id:
                self.logger.error("存储配置缺少ID")
                return False
            
            self.logger.debug(f"测试NFS存储连接: {server}:{path}")
            
            # 使用mount_manager进行测试挂载
            mount_point = self.mount_manager.mount_storage(storage_id, storage_config)
            
            if mount_point:
                self.logger.info(f"NFS存储连接测试成功: {mount_point}")
                
                # 测试基本的文件系统操作
                try:
                    # 测试读取目录
                    if os.path.exists(mount_point) and os.path.isdir(mount_point):
                        os.listdir(mount_point)  # 简单的目录列表测试
                        self.logger.debug("NFS目录读取测试成功")
                        return True
                    else:
                        self.logger.warning(f"挂载点不是有效目录: {mount_point}")
                        return False
                        
                except Exception as e:
                    self.logger.warning(f"NFS目录访问测试失败: {e}")
                    # 即使目录访问失败，如果挂载成功，也认为连接正常
                    return True
            else:
                self.logger.error("NFS存储挂载失败")
                return False
                
        except Exception as e:
            self.logger.error(f"NFS检查时出错: {e}")
            return False
    
    def _check_obs(self, storage_config: Dict[str, Any]) -> bool:
        """检查OBS是否可以访问"""
        try:
            # 检查OBS配置
            provider = storage_config.get('provider')
            access_key = storage_config.get('access_key')
            secret_key = storage_config.get('secret_key')
            region = storage_config.get('region')
            endpoint = storage_config.get('endpoint')
            bucket = storage_config.get('bucket')
            
            self.logger.debug(f"OBS配置检查 - provider: {provider}, region: {region}, endpoint: {endpoint}, bucket: {bucket}")
            
            if not provider or not access_key or not secret_key or not region or not endpoint or not bucket:
                self.logger.error(f"OBS配置缺少必需字段: provider={provider}, access_key={'***' if access_key else 'None'}, region={region}, endpoint={endpoint}, bucket={bucket}")
                return False

            # 使用rclone检查OBS配置
            rclone_config, remote_name = self._create_rclone_config(storage_config)
            
            # 检查桶是否存在
            self.logger.debug(f"检查OBS桶是否存在: {bucket}")
            cmd_check_bucket = ['rclone', '--config', rclone_config, 'lsd', f"{remote_name}:"]
            self.logger.debug(f"执行OBS桶检查命令: {' '.join(cmd_check_bucket)}")
            
            result = subprocess.run(cmd_check_bucket, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"OBS桶检查失败: {result.stderr}")
                # 尝试列出所有桶
                cmd_list_buckets = ['rclone', '--config', rclone_config, 'listremotes']
                self.logger.debug(f"尝试列出所有远程存储: {' '.join(cmd_list_buckets)}")
                list_result = subprocess.run(cmd_list_buckets, capture_output=True, text=True, timeout=30)
                if list_result.returncode == 0:
                    self.logger.debug(f"可用的远程存储: {list_result.stdout}")
                return False
            
            self.logger.debug(f"OBS桶检查成功: {result.stdout[:200]}...")
            return True
                
        except subprocess.TimeoutExpired:
            self.logger.error("OBS检查超时")
            return False
        except Exception as e:
            self.logger.error(f"检查OBS时出错: {e}")
            return False
        finally:
            if 'rclone_config' in locals():
                os.unlink(rclone_config)
    
    def sync_data(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                 options: Dict[str, Any] = None, progress_callback: Optional[Callable] = None,
                 source_path: str = None, target_path: str = None, process_callback: Optional[Callable] = None,
                 task_id: str = None) -> bool:
        """同步数据
        
        Args:
            source_config: 源存储配置
            target_config: 目标存储配置
            options: 同步选项
            progress_callback: 进度回调
            source_path: 源端路径（可选）
            target_path: 目标端路径（可选）
        """
        try:
            source_type = source_config['type']
            target_type = target_config['type']
            
            self.logger.info(f"开始同步: {source_type} -> {target_type}")
            if source_path:
                self.logger.info(f"源端路径: {source_path}")
            if target_path:
                self.logger.info(f"目标端路径: {target_path}")
            
            # 创建进度监控器
            monitor = ProgressMonitor(progress_callback)
            monitor.start()
            
            # 查找对应的同步方法
            sync_key = (source_type, target_type)
            if sync_key in self.sync_methods:
                sync_method = self.sync_methods[sync_key]
                return sync_method(source_config, target_config, options, monitor, source_path, target_path, task_id)
            else:
                raise ValueError(f"Unsupported sync combination: {source_type} -> {target_type}")
                
        except Exception as e:
            self.logger.error(f"Error syncing data: {e}")
            raise
            
    def _sync_nfs_to_obs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                        options: Dict[str, Any], monitor: ProgressMonitor,
                        source_path: str = None, target_path: str = None, task_id: str = None) -> bool:
        """NFS/NAS -> OBS 同步"""
        try:
            # 挂载NFS
            source_mount = self.mount(source_config)
            
            # 创建临时的rclone配置
            rclone_config, remote_name = self._create_rclone_config(target_config)
            
            try:
                # 构建源端路径
                source_full_path = source_mount
                if source_path:
                    source_full_path = f"{source_mount}/{source_path}"
                
                # 构建目标端路径 - 使用线程唯一的远程存储名称
                target_full_path = f"{remote_name}:"
                if target_path:
                    target_full_path = f"{remote_name}:{target_path}"
                
                self.logger.info(f"NFS -> OBS 同步路径: {source_full_path} -> {target_full_path}")
                
                # 使用rclone同步到OBS，启用JSON日志格式
                cmd = ['rclone', '--config', rclone_config, 'sync', '--use-json-log', '--log-level', 'NOTICE', '--stats-log-level', 'NOTICE', '--stats', '1s']
                
                # 添加选项 - 只添加有效的rclone选项
                if options:
                    # 处理带宽限制
                    if options.get('bandwidth_limit', 0) > 0:
                        cmd.extend(['--bwlimit', str(options['bandwidth_limit'])])
                    
                    # 处理校验和
                    if options.get('checksum', False):
                        cmd.extend(['--checksum'])
                
                    # 处理删除
                    if options.get('delete', False):
                        cmd.extend(['--delete'])
                    
                    # 处理最大连接数
                    if options.get('max_connections', 0) > 0:
                        cmd.extend(['--transfers', str(options['max_connections'])])
                    
                    # 处理重试选项
                    retry_options = options.get('retry_options', {})
                    if retry_options:
                        max_retries = retry_options.get('max_retries', 3)
                        retry_interval = retry_options.get('retry_interval', 30)
                        cmd.extend(['--retries', str(max_retries)])
                        cmd.extend(['--retries-sleep', f"{retry_interval}s"])
                        
                # 添加源和目标
                cmd.extend([source_full_path, target_full_path])
                
                self.logger.debug(f"执行同步命令: {' '.join(cmd)}")
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # 注册进程到任务管理器（如果可用）
                if task_id and hasattr(self, 'task_manager') and self.task_manager:
                    try:
                        self.task_manager.register_task(task_id, process)
                        self.logger.info(f"注册任务 {task_id} 到任务管理器")
                    except Exception as e:
                        self.logger.warning(f"注册任务到任务管理器失败: {e}")
                
                # 监控进度 - 从stderr读取JSON日志
                while True:
                    line = process.stderr.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    stderr_output = process.stderr.read()
                    self.logger.error(f"同步失败: {stderr_output}")
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
                         options: Dict[str, Any], monitor: ProgressMonitor,
                         source_path: str = None, target_path: str = None, task_id: str = None) -> bool:
        """NFS/NAS -> NFS/NAS 同步"""
        try:
            # 挂载源NFS
            source_mount = self.mount(source_config)
            
            # 挂载目标NFS
            target_mount = self.mount(target_config)
            
            try:
                # 构建源端路径
                source_full_path = source_mount
                if source_path:
                    source_full_path = f"{source_mount}/{source_path}"
                
                # 构建目标端路径
                target_full_path = target_mount
                if target_path:
                    # 确保目标目录存在
                    target_dir = f"{target_mount}/{target_path}"
                    os.makedirs(target_dir, exist_ok=True)
                    target_full_path = target_dir
                
                self.logger.info(f"NFS -> NFS 同步路径: {source_full_path} -> {target_full_path}")
                
                # 快速估算数据量（可选，避免大数据量的dry-run）
                use_quick_estimate = self._should_use_quick_estimate(source_full_path)
                
                if use_quick_estimate:
                    # 使用快速估算
                    total_files, total_size = self._quick_estimate_sync_size(source_full_path)
                    self.logger.info(f"快速估算: {total_files} 文件, {total_size} 字节")
                else:
                    # 使用dry-run获取准确信息（仅适用于小数据量）
                    dry_run_cmd = ['rsync', '-a', '--dry-run', '--stats', f"{source_full_path}/", target_full_path]
                    self.logger.debug(f"执行dry-run命令: {' '.join(dry_run_cmd)}")
                    
                    dry_run_result = subprocess.run(dry_run_cmd, capture_output=True, text=True, timeout=60)
                    if dry_run_result.returncode != 0:
                        self.logger.warning(f"Dry-run失败，将使用快速估算: {dry_run_result.stderr}")
                        total_files, total_size = self._quick_estimate_sync_size(source_full_path)
                    else:
                        # 解析dry-run输出获取总信息
                        total_files, total_size = self._parse_rsync_stats(dry_run_result.stdout)
                        self.logger.info(f"Dry-run结果: {total_files} 文件, {total_size} 字节")
                
                # 通知进度监控器总信息
                if hasattr(monitor, 'total_files'):
                    monitor.total_files = total_files
                if hasattr(monitor, 'total_size'):
                    monitor.total_size = total_size
                
                # 实际同步，使用progress2输出
                cmd = ['rsync', '-a', '--info=progress2']
                
                # 添加选项
                if options:
                    for key, value in options.items():
                        if key == 'delete':
                            if value:
                                cmd.append('--delete')
                        elif key == 'compress':
                            if value:
                                cmd.append('--compress')
                        elif key == 'checksum':
                            if value:
                                cmd.append('--checksum')
                        elif key == 'bandwidth_limit':
                            cmd.extend(['--bwlimit', str(value)])
                
                # 添加源和目标
                cmd.extend([f"{source_full_path}/", target_full_path])
                
                self.logger.debug(f"执行同步命令: {' '.join(cmd)}")
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                # 注册进程到任务管理器（如果可用）
                if task_id and hasattr(self, 'task_manager') and self.task_manager:
                    try:
                        self.task_manager.register_task(task_id, process)
                        self.logger.info(f"注册任务 {task_id} 到任务管理器")
                    except Exception as e:
                        self.logger.warning(f"注册任务到任务管理器失败: {e}")
                
                # 监控进度
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rsync_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    stderr_output = process.stderr.read()
                    self.logger.error(f"同步失败: {stderr_output}")
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                # 清理资源
                self.unmount(source_mount)
                self.unmount(target_mount)
                
        except Exception as e:
            self.logger.error(f"Error in NFS/NAS to NFS/NAS sync: {e}")
            raise
            
    def _should_use_quick_estimate(self, source_path: str) -> bool:
        """判断是否应该使用快速估算而不是dry-run"""
        try:
            # 轻量级检查：只检查顶层文件和目录数量
            # 避免使用du命令，因为它对大目录很慢
            
            # 快速检查顶层目录和文件数量
            ls_cmd = ['ls', '-la', source_path]
            result = subprocess.run(ls_cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # 去除总计行和当前/父目录项
                items = [line for line in lines if not line.startswith('total') and 
                        not line.endswith(' .') and not line.endswith(' ..')]
                item_count = len(items)
                
                # 如果顶层就有很多项目（超过100个），很可能是大目录
                if item_count > 100:
                    self.logger.info(f"顶层有 {item_count} 个项目，使用快速估算")
                    return True
            
            # 检查一级子目录的数量（限制深度为1，超时短）
            find_cmd = ['find', source_path, '-maxdepth', '1', '-type', 'd']
            result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                dir_count = len(result.stdout.strip().split('\n')) - 1  # 减去根目录本身
                
                # 如果一级子目录超过50个，很可能是大目录结构
                if dir_count > 50:
                    self.logger.info(f"一级子目录数量 {dir_count}，使用快速估算")
                    return True
                    
        except Exception as e:
            self.logger.warning(f"轻量级目录检查失败: {e}")
            # 如果检查失败，默认使用快速估算（更安全）
            self.logger.info("检查失败，默认使用快速估算")
            return True
            
        return False
        
    def _quick_estimate_sync_size(self, source_path: str) -> tuple:
        """快速估算同步大小"""
        try:
            # 使用du命令快速获取目录大小
            du_cmd = ['du', '-sb', source_path]
            result = subprocess.run(du_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                size_str = result.stdout.split()[0]
                total_size = int(size_str)
                
                # 快速估算文件数量（只检查前几层目录）
                find_cmd = ['find', source_path, '-type', 'f', '-maxdepth', '3']
                result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    file_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                    
                    # 基于检查的文件数估算总文件数
                    # 假设前3层目录的文件数占总数的30%
                    estimated_total_files = int(file_count / 0.3) if file_count > 0 else 100
                    
                    self.logger.debug(f"快速估算: {estimated_total_files} 文件, {total_size} 字节")
                    return estimated_total_files, total_size
                    
        except Exception as e:
            self.logger.warning(f"快速估算失败: {e}")
            
        # 如果估算失败，返回默认值
        return 100, 1024 * 1024  # 100个文件，1MB
    
    def _parse_rsync_stats(self, output: str) -> tuple:
        """从rsync的--dry-run输出中解析总文件数和总大小"""
        total_files = 0
        total_size = 0
        
        for line in output.splitlines():
            if line.startswith('Number of files: '):
                # 解析格式: "Number of files: 28,136 (reg: 4,886, dir: 23,250)"
                # 只提取第一个数字部分
                files_str = line.replace('Number of files: ', '').strip()
                # 提取第一个数字（可能包含逗号）
                files_match = re.search(r'(\d+(?:,\d+)*)', files_str)
                if files_match:
                    # 移除逗号并转换为整数
                    total_files = int(files_match.group(1).replace(',', ''))
                else:
                    self.logger.warning(f"无法解析文件数: {files_str}")
            elif line.startswith('Total transferred: '):
                # 从 'Total transferred: N (XXX bytes)' 中提取字节数
                match = re.search(r'Total transferred: (\d+) \((\d+) bytes\)', line)
                if match:
                    total_size = int(match.group(2))
                    break # 找到第一个匹配的行即可
        
        return total_files, total_size
    
    def _sync_obs_to_obs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                        options: Dict[str, Any], monitor: ProgressMonitor,
                        source_path: str = None, target_path: str = None, task_id: str = None) -> bool:
        """OBS -> OBS 同步"""
        try:
            # 创建包含源和目标两个远程存储的rclone配置
            rclone_config, source_remote_name, target_remote_name = self._create_dual_rclone_config(source_config, target_config)
            
            try:
                # 构建源端路径
                source_full_path = f"{source_remote_name}:"
                if source_path:
                    source_full_path = f"{source_remote_name}:{source_path}"
                
                # 构建目标端路径
                target_full_path = f"{target_remote_name}:"
                if target_path:
                    target_full_path = f"{target_remote_name}:{target_path}"
                
                self.logger.info(f"OBS -> OBS 同步路径: {source_full_path} -> {target_full_path}")
                
                # 使用rclone同步
                cmd = ['rclone', '--config', rclone_config, 'sync', '--use-json-log', '--log-level', 'NOTICE', '--stats-log-level', 'NOTICE', '--stats', '1s']
                
                # 添加选项 - 只添加有效的rclone选项
                if options:
                    # 处理带宽限制
                    if options.get('bandwidth_limit', 0) > 0:
                        cmd.extend(['--bwlimit', str(options['bandwidth_limit'])])
                    
                    # 处理校验和
                    if options.get('checksum', False):
                        cmd.extend(['--checksum'])
                    
                    # 处理最大连接数
                    if options.get('max_connections', 0) > 0:
                        cmd.extend(['--transfers', str(options['max_connections'])])
                    
                    # 处理重试选项
                    retry_options = options.get('retry_options', {})
                    if retry_options:
                        max_retries = retry_options.get('max_retries', 3)
                        retry_interval = retry_options.get('retry_interval', 30)
                        cmd.extend(['--retries', str(max_retries)])
                        cmd.extend(['--retries-sleep', f"{retry_interval}s"])
                        
                # 添加源和目标
                cmd.extend([source_full_path, target_full_path])
                
                self.logger.debug(f"执行同步命令: {' '.join(cmd)}")
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                # 注册进程到任务管理器（如果可用）
                if task_id and hasattr(self, 'task_manager') and self.task_manager:
                    try:
                        self.task_manager.register_task(task_id, process)
                        self.logger.info(f"注册任务 {task_id} 到任务管理器")
                    except Exception as e:
                        self.logger.warning(f"注册任务到任务管理器失败: {e}")

                # 监控进度 - 从stderr读取JSON日志
                while True:
                    line = process.stderr.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    stderr_output = process.stderr.read()
                    self.logger.error(f"同步失败: {stderr_output}")
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                # 清理资源
                os.unlink(rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in OBS to OBS sync: {e}")
            raise
            
    def _sync_obs_to_nfs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                         options: Dict[str, Any], monitor: ProgressMonitor,
                         source_path: str = None, target_path: str = None, task_id: str = None) -> bool:
        """OBS -> NFS/NAS 同步"""
        try:
            # 挂载目标NFS (使用统一的mount方法)
            target_mount = self.mount(target_config)
            
            # 创建临时的rclone配置
            rclone_config, remote_name = self._create_rclone_config(source_config)
            
            try:
                # 构建源端路径 - 使用线程唯一的远程存储名称
                source_full_path = f"{remote_name}:"
                if source_path:
                    source_full_path = f"{remote_name}:{source_path}"
                
                # 构建目标端路径
                target_full_path = target_mount
                if target_path:
                    # 确保目标目录存在
                    target_dir = f"{target_mount}/{target_path}"
                    os.makedirs(target_dir, exist_ok=True)
                    target_full_path = target_dir
                
                self.logger.info(f"OBS -> NFS 同步路径: {source_full_path} -> {target_full_path}")
                
                # 使用rclone同步
                cmd = ['rclone', '--config', rclone_config, 'sync', '--use-json-log', '--log-level', 'NOTICE', '--stats-log-level', 'NOTICE', '--stats', '1s']
                
                # 添加选项 - 只添加有效的rclone选项
                if options:
                    # 处理带宽限制
                    if options.get('bandwidth_limit', 0) > 0:
                        cmd.extend(['--bwlimit', str(options['bandwidth_limit'])])
                    
                    # 处理校验和
                    if options.get('checksum', False):
                        cmd.append('--checksum')
                    
                    # 处理连接数
                    if options.get('max_connections', 1) > 1:
                        cmd.extend(['--transfers', str(options['max_connections'])])
                    
                    # 处理重试选项
                    retry_options = options.get('retry_options', {})
                    if retry_options:
                        max_retries = retry_options.get('max_retries', 3)
                        retry_interval = retry_options.get('retry_interval', 30)
                        cmd.extend(['--retries', str(max_retries)])
                        cmd.extend(['--retries-sleep', f"{retry_interval}s"])
                        
                # 添加源和目标
                cmd.extend([source_full_path, target_full_path])
                
                self.logger.debug(f"执行同步命令: {' '.join(cmd)}")
                
                # 执行同步
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                # 注册进程到任务管理器（如果可用）
                if task_id and hasattr(self, 'task_manager') and self.task_manager:
                    try:
                        self.task_manager.register_task(task_id, process)
                        self.logger.info(f"注册任务 {task_id} 到任务管理器")
                    except Exception as e:
                        self.logger.warning(f"注册任务到任务管理器失败: {e}")
                
                # 监控进度 - 从stderr读取JSON日志
                while True:
                    line = process.stderr.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                # 检查结果
                if process.returncode != 0:
                    stderr_output = process.stderr.read()
                    self.logger.error(f"同步失败: {stderr_output}")
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                # 清理资源
                self.unmount(target_mount)
                os.unlink(rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in OBS to NFS/NAS sync: {e}")
            raise
            
    def cleanup_all_mounts(self):
        """清理所有挂载点"""
        try:
            # 使用挂载管理器清理所有挂载点
            cleaned_count = self.mount_manager.cleanup_abandoned_mounts()
            self.logger.info(f"清理了 {cleaned_count} 个废弃的挂载点")
            
            # 清理easysync挂载目录
            import shutil
            try:
                if os.path.exists("/tmp/easysync_mounts"):
                    shutil.rmtree("/tmp/easysync_mounts")
                    self.logger.info("清理了 easysync 挂载目录")
            except Exception as e:
                self.logger.warning(f"清理挂载目录失败: {e}")
                
        except Exception as e:
            self.logger.error(f"清理挂载点时出错: {e}")
    
    def list_mounts(self) -> Dict[str, Dict[str, Any]]:
        """列出所有挂载点"""
        return self.mount_manager.get_active_mounts()
        
    def get_mount_info(self, mount_point: str) -> Optional[Dict[str, Any]]:
        """获取挂载点信息"""
        active_mounts = self.mount_manager.get_active_mounts()
        for storage_id, mount_info in active_mounts.items():
            if mount_info.get('mount_point') == mount_point:
                return mount_info
        return None
        
    def check_mount(self, storage_config: Dict[str, Any]) -> Dict[str, Any]:
        """检查存储挂载状态
        
        使用 mount_manager 进行检查
        
        Args:
            storage_config: 存储配置
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        try:
            storage_type = storage_config.get('type')
            result = {
                'type': storage_type,
                'available': False,
                'mounted': False,
                'error': None,
                'details': {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 生成存储ID
            storage_id = self._generate_storage_id(storage_config)
            
            # 使用 mount_manager 检查挂载状态
            if self.mount_manager.is_mounted(storage_id):
                result.update({
                    'available': True,
                    'mounted': True,
                    'mount_point': self.mount_manager.get_mount_point(storage_id)
                })
            else:
                result.update({
                    'available': False,
                    'mounted': False,
                    'error': 'Storage not mounted'
                })
                
            return result
            
        except Exception as e:
            self.logger.error(f"检查挂载状态失败: {e}")
            return {
                'type': storage_config.get('type'),
                'available': False,
                'mounted': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def copy_data(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                 options: Dict[str, Any] = None, progress_callback: Optional[Callable] = None) -> bool:
        """复制数据（与sync_data类似，但使用copy而非sync）"""
        try:
            source_type = source_config['type']
            target_type = target_config['type']
            
            # 创建进度监控器
            monitor = ProgressMonitor(progress_callback)
            monitor.start()
            
            # 查找对应的复制方法
            copy_key = (source_type, target_type)
            if copy_key in self.copy_methods:
                copy_method = self.copy_methods[copy_key]
                return copy_method(source_config, target_config, options, monitor)
            else:
                raise ValueError(f"Unsupported copy combination: {source_type} -> {target_type}")
                
        except Exception as e:
            self.logger.error(f"Error copying data: {e}")
            raise
            
    def _copy_nfs_to_obs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                        options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """NFS/NAS -> OBS 复制"""
        try:
            source_mount = self.mount(source_config)
            rclone_config = self._create_rclone_config(target_config)
            
            try:
                cmd = ['rclone', '--config', rclone_config, 'copy', '-P']
                
                if options:
                    for key, value in options.items():
                        cmd.extend([f'--{key}', str(value)])
                        
                cmd.extend([source_mount, f"temp:{target_config['bucket']}/{target_config['path']}"])
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                self.unmount(source_mount)
                os.unlink(rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in NFS/NAS to OBS copy: {e}")
            raise
            
    def _copy_nfs_to_nfs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                         options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """NFS/NAS -> NFS/NAS 复制"""
        try:
            source_mount = self.mount(source_config)
            target_mount = self.mount(target_config)
            
            try:
                cmd = ['rsync', '-avz']
                
                if options:
                    if options.get('exclude'):
                        for pattern in options['exclude']:
                            cmd.extend(['--exclude', pattern])
                    if options.get('include'):
                        for pattern in options['include']:
                            cmd.extend(['--include', pattern])
                            
                cmd.extend([source_mount, target_mount])
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                # 注册进程到任务管理器（如果可用）
                if task_id and hasattr(self, 'task_manager') and self.task_manager:
                    try:
                        self.task_manager.register_task(task_id, process)
                        self.logger.info(f"注册任务 {task_id} 到任务管理器")
                    except Exception as e:
                        self.logger.warning(f"注册任务到任务管理器失败: {e}")
                            
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rsync_progress(line)
                        
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                self.unmount(source_mount)
                self.unmount(target_mount)
                
        except Exception as e:
            self.logger.error(f"Error in NFS/NAS to NFS/NAS copy: {e}")
            raise
            
    def _copy_obs_to_obs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                        options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """OBS -> OBS 复制"""
        try:
            source_rclone_config = self._create_rclone_config(source_config)
            target_rclone_config = self._create_rclone_config(target_config)
            
            try:
                cmd = ['rclone', '--config', source_rclone_config, 'copy', '-P']
                
                if options:
                    for key, value in options.items():
                        cmd.extend([f'--{key}', str(value)])
                        
                cmd.extend([
                    f"temp:{source_config['bucket']}/{source_config['path']}",
                    f"temp:{target_config['bucket']}/{target_config['path']}"
                ])
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                os.unlink(source_rclone_config)
                os.unlink(target_rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in OBS to OBS copy: {e}")
            raise
            
    def _copy_obs_to_nfs(self, source_config: Dict[str, Any], target_config: Dict[str, Any], 
                         options: Dict[str, Any], monitor: ProgressMonitor) -> bool:
        """OBS -> NFS/NAS 复制"""
        try:
            target_mount = self.mount(target_config)
            rclone_config = self._create_rclone_config(source_config)
            
            try:
                cmd = ['rclone', '--config', rclone_config, 'copy', '-P']
                
                if options:
                    for key, value in options.items():
                        cmd.extend([f'--{key}', str(value)])
                        
                cmd.extend([f"temp:{source_config['bucket']}/{source_config['path']}", target_mount])
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        monitor.update_rclone_progress(line)
                        
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd)
                    
                return True
                
            finally:
                self.unmount(target_mount)
                os.unlink(rclone_config)
                
        except Exception as e:
            self.logger.error(f"Error in OBS to NFS/NAS copy: {e}")
            raise 