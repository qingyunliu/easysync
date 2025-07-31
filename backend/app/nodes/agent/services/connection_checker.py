#!/usr/bin/env python3
"""
存储连接检查器 - 提供全面的存储连接和挂载检查功能
"""

import logging
import subprocess
import socket
import time
import os
import tempfile
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import json

class CheckStatus(Enum):
    """检查状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class ConnectionResult:
    """连接检查结果"""
    status: CheckStatus
    message: str
    details: Dict[str, Any]
    check_time: datetime
    response_time: float
    error: Optional[str] = None

@dataclass
class MountResult:
    """挂载检查结果"""
    status: CheckStatus
    mount_point: str
    is_mounted: bool
    mount_info: Dict[str, Any]
    check_time: datetime
    error: Optional[str] = None

class StorageConnectionChecker:
    """存储连接检查器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('StorageConnectionChecker')
        
        # 检查配置
        self.timeout = config.get('connection_check', {}).get('timeout', 30)
        self.retry_count = config.get('connection_check', {}).get('retry_count', 3)
        self.retry_delay = config.get('connection_check', {}).get('retry_delay', 2)
        
        # 检查历史记录
        self.check_history: Dict[str, List[ConnectionResult]] = {}
        self.history_lock = threading.Lock()
        
        # 临时目录
        self.temp_dir = tempfile.mkdtemp(prefix='easysync_check_')
    
    def check_storage_connection(self, storage_config: Dict[str, Any]) -> ConnectionResult:
        """检查存储连接"""
        storage_type = storage_config.get('type', '').lower()
        
        check_functions = {
            'nas': self._check_nas_connection,
            's3': self._check_s3_connection,
            'obs': self._check_obs_connection,
            'local': self._check_local_connection
        }
        
        if storage_type not in check_functions:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"不支持的存储类型: {storage_type}",
                details={},
                check_time=datetime.now(),
                response_time=0.0,
                error=f"Unknown storage type: {storage_type}"
            )
        
        # 执行检查
        start_time = time.time()
        try:
            result = check_functions[storage_type](storage_config)
            result.response_time = time.time() - start_time
            
            # 保存检查历史
            self._save_check_history(storage_config.get('id', 'unknown'), result)
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            result = ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"检查失败: {str(e)}",
                details={},
                check_time=datetime.now(),
                response_time=response_time,
                error=str(e)
            )
            
            self._save_check_history(storage_config.get('id', 'unknown'), result)
            return result
    
    def _check_nas_connection(self, storage_config: Dict[str, Any]) -> ConnectionResult:
        """检查NAS连接"""
        config = storage_config.get('config', {})
        host = config.get('host') or config.get('server')  # 兼容两种字段名
        port = config.get('port', 2049)  # NFS默认端口
        protocol = config.get('protocol', 'nfs').lower()
        
        if not host:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message="NAS配置中缺少服务器地址",
                details={},
                check_time=datetime.now(),
                response_time=0.0,
                error="Missing server/host in NAS config"
            )
        
        details = {
            'host': host,
            'port': port,
            'protocol': protocol
        }
        
        # 检查网络连接
        network_result = self._check_network_connection(host, port)
        if network_result.status != CheckStatus.SUCCESS:
            return ConnectionResult(
                status=network_result.status,
                message=f"无法连接到 {host}:{port}",
                details=details,
                check_time=datetime.now(),
                response_time=0.0,
                error=network_result.error
            )
        
        # 检查SMB/NFS服务
        if protocol == 'smb':
            return self._check_smb_service(config, details)
        elif protocol == 'nfs':
            return self._check_nfs_service(config, details)
        else:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"不支持的协议: {protocol}",
                details=details,
                check_time=datetime.now(),
                response_time=0.0,
                error=f"Unsupported protocol: {protocol}"
            )
    
    def _check_s3_connection(self, storage_config: Dict[str, Any]) -> ConnectionResult:
        """检查S3连接"""
        config = storage_config.get('config', {})
        access_key = config.get('access_key')
        secret_key = config.get('secret_key')
        region = config.get('region', 'us-east-1')
        endpoint = config.get('endpoint')
        bucket = config.get('bucket')
        
        if not all([access_key, secret_key]):
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message="S3配置中缺少访问密钥",
                details={},
                check_time=datetime.now(),
                response_time=0.0,
                error="Missing access keys in S3 config"
            )
        
        details = {
            'region': region,
            'endpoint': endpoint,
            'bucket': bucket,
            'access_key': access_key[:8] + '...' if access_key else None
        }
        
        try:
            # 使用rclone检查S3连接
            result = self._check_s3_with_rclone(config, details)
            return result
            
        except Exception as e:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"S3连接检查失败: {str(e)}",
                details=details,
                check_time=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _check_obs_connection(self, storage_config: Dict[str, Any]) -> ConnectionResult:
        """检查OBS连接（华为云对象存储）"""
        # OBS基本上兼容S3 API
        return self._check_s3_connection(storage_config)
    
    def _check_local_connection(self, storage_config: Dict[str, Any]) -> ConnectionResult:
        """检查本地存储连接"""
        config = storage_config.get('config', {})
        base_path = config.get('base_path', '/data')
        
        details = {
            'base_path': base_path,
            'type': 'local'
        }
        
        try:
            # 检查目录是否存在
            if not os.path.exists(base_path):
                return ConnectionResult(
                    status=CheckStatus.FAILED,
                    message=f"目录不存在: {base_path}",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0,
                    error=f"Directory not found: {base_path}"
                )
            
            # 检查是否可读写
            if not os.access(base_path, os.R_OK | os.W_OK):
                return ConnectionResult(
                    status=CheckStatus.WARNING,
                    message=f"目录权限不足: {base_path}",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0,
                    error=f"Insufficient permissions: {base_path}"
                )
            
            # 检查磁盘空间
            statvfs = os.statvfs(base_path)
            free_space = statvfs.f_frsize * statvfs.f_bavail
            total_space = statvfs.f_frsize * statvfs.f_blocks
            
            details.update({
                'free_space': free_space,
                'total_space': total_space,
                'free_space_gb': free_space / (1024**3),
                'total_space_gb': total_space / (1024**3)
            })
            
            # 检查可用空间是否足够（至少1GB）
            if free_space < 1024**3:
                return ConnectionResult(
                    status=CheckStatus.WARNING,
                    message=f"磁盘空间不足: {free_space / (1024**3):.2f}GB",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0
                )
            
            return ConnectionResult(
                status=CheckStatus.SUCCESS,
                message="本地存储连接正常",
                details=details,
                check_time=datetime.now(),
                response_time=0.0
            )
            
        except Exception as e:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"本地存储检查失败: {str(e)}",
                details=details,
                check_time=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _check_network_connection(self, host: str, port: int) -> ConnectionResult:
        """检查网络连接"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            result = sock.connect_ex((host, port))
            response_time = time.time() - start_time
            
            sock.close()
            
            if result == 0:
                return ConnectionResult(
                    status=CheckStatus.SUCCESS,
                    message=f"网络连接正常: {host}:{port}",
                    details={'host': host, 'port': port},
                    check_time=datetime.now(),
                    response_time=response_time
                )
            else:
                return ConnectionResult(
                    status=CheckStatus.FAILED,
                    message=f"网络连接失败: {host}:{port}",
                    details={'host': host, 'port': port},
                    check_time=datetime.now(),
                    response_time=response_time,
                    error=f"Connection failed with code: {result}"
                )
                
        except socket.timeout:
            return ConnectionResult(
                status=CheckStatus.TIMEOUT,
                message=f"网络连接超时: {host}:{port}",
                details={'host': host, 'port': port},
                check_time=datetime.now(),
                response_time=self.timeout,
                error="Connection timeout"
            )
        except Exception as e:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"网络连接异常: {str(e)}",
                details={'host': host, 'port': port},
                check_time=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _check_smb_service(self, config: Dict[str, Any], details: Dict[str, Any]) -> ConnectionResult:
        """检查SMB服务"""
        try:
            # 使用smbclient检查SMB连接
            host = config.get('server') or config.get('host')
            share_path = config.get('path', '')  # 前端发送的是 path
            username = config.get('username', '')
            password = config.get('password', '')
            
            cmd = ['smbclient', f"//{host}{share_path}", '-U', f"{username}%{password}", '-c', 'ls']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return ConnectionResult(
                    status=CheckStatus.SUCCESS,
                    message="SMB服务连接正常",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0
                )
            else:
                return ConnectionResult(
                    status=CheckStatus.FAILED,
                    message=f"SMB连接失败: {result.stderr}",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0,
                    error=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            return ConnectionResult(
                status=CheckStatus.TIMEOUT,
                message="SMB连接超时",
                details=details,
                check_time=datetime.now(),
                response_time=self.timeout,
                error="SMB connection timeout"
            )
        except Exception as e:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"SMB检查异常: {str(e)}",
                details=details,
                check_time=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _check_nfs_service(self, config: Dict[str, Any], details: Dict[str, Any]) -> ConnectionResult:
        """检查NFS服务"""
        try:
            # 使用showmount检查NFS导出
            host = config.get('server') or config.get('host')
            
            cmd = ['showmount', '-e', host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                exports = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                details['exports'] = exports
                
                return ConnectionResult(
                    status=CheckStatus.SUCCESS,
                    message="NFS服务连接正常",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0
                )
            else:
                return ConnectionResult(
                    status=CheckStatus.FAILED,
                    message=f"NFS连接失败: {result.stderr}",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0,
                    error=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            return ConnectionResult(
                status=CheckStatus.TIMEOUT,
                message="NFS连接超时",
                details=details,
                check_time=datetime.now(),
                response_time=self.timeout,
                error="NFS connection timeout"
            )
        except Exception as e:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"NFS检查异常: {str(e)}",
                details=details,
                check_time=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _check_s3_with_rclone(self, config: Dict[str, Any], details: Dict[str, Any]) -> ConnectionResult:
        """使用rclone检查S3连接"""
        try:
            # 创建临时rclone配置
            config_file = self._create_temp_rclone_config(config)
            
            # 使用rclone lsd命令检查连接
            cmd = ['rclone', 'lsd', 'temp_s3:', '--config', config_file]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # 清理临时配置文件
            os.unlink(config_file)
            
            if result.returncode == 0:
                return ConnectionResult(
                    status=CheckStatus.SUCCESS,
                    message="S3连接正常",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0
                )
            else:
                return ConnectionResult(
                    status=CheckStatus.FAILED,
                    message=f"S3连接失败: {result.stderr}",
                    details=details,
                    check_time=datetime.now(),
                    response_time=0.0,
                    error=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            return ConnectionResult(
                status=CheckStatus.TIMEOUT,
                message="S3连接超时",
                details=details,
                check_time=datetime.now(),
                response_time=self.timeout,
                error="S3 connection timeout"
            )
        except Exception as e:
            return ConnectionResult(
                status=CheckStatus.FAILED,
                message=f"S3检查异常: {str(e)}",
                details=details,
                check_time=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _create_temp_rclone_config(self, config: Dict[str, Any]) -> str:
        """创建临时rclone配置文件"""
        config_content = f"""[temp_s3]
type = s3
access_key_id = {config['access_key']}
secret_access_key = {config['secret_key']}
region = {config.get('region', 'us-east-1')}
"""
        
        if config.get('endpoint'):
            config_content += f"endpoint = {config['endpoint']}\n"
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False)
        temp_file.write(config_content)
        temp_file.close()
        
        return temp_file.name
    
    def _save_check_history(self, storage_id: str, result: ConnectionResult):
        """保存检查历史"""
        with self.history_lock:
            if storage_id not in self.check_history:
                self.check_history[storage_id] = []
            
            self.check_history[storage_id].append(result)
            
            # 限制历史记录数量
            max_history = self.config.get('connection_check', {}).get('max_history', 100)
            if len(self.check_history[storage_id]) > max_history:
                self.check_history[storage_id].pop(0)
    
    def get_check_history(self, storage_id: str) -> List[ConnectionResult]:
        """获取检查历史"""
        with self.history_lock:
            return self.check_history.get(storage_id, [])
    
    def cleanup(self):
        """清理资源"""
        try:
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.error(f"清理临时目录失败: {e}")

class MountChecker:
    """挂载检查器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('MountChecker')
        
        # 挂载检查历史
        self.mount_history: Dict[str, List[MountResult]] = {}
        self.history_lock = threading.Lock()
    
    def check_mount_status(self, mount_point: str) -> MountResult:
        """检查挂载状态"""
        try:
            # 检查挂载点是否存在
            if not os.path.exists(mount_point):
                return MountResult(
                    status=CheckStatus.FAILED,
                    mount_point=mount_point,
                    is_mounted=False,
                    mount_info={},
                    check_time=datetime.now(),
                    error="Mount point does not exist"
                )
            
            # 检查是否已挂载
            mount_info = self._get_mount_info(mount_point)
            is_mounted = mount_info is not None
            
            if is_mounted:
                # 检查挂载点是否可访问
                accessible = self._test_mount_access(mount_point)
                
                if accessible:
                    result = MountResult(
                        status=CheckStatus.SUCCESS,
                        mount_point=mount_point,
                        is_mounted=True,
                        mount_info=mount_info,
                        check_time=datetime.now()
                    )
                else:
                    result = MountResult(
                        status=CheckStatus.WARNING,
                        mount_point=mount_point,
                        is_mounted=True,
                        mount_info=mount_info,
                        check_time=datetime.now(),
                        error="Mount point is not accessible"
                    )
            else:
                result = MountResult(
                    status=CheckStatus.FAILED,
                    mount_point=mount_point,
                    is_mounted=False,
                    mount_info={},
                    check_time=datetime.now(),
                    error="Not mounted"
                )
            
            # 保存检查历史
            self._save_mount_history(mount_point, result)
            
            return result
            
        except Exception as e:
            result = MountResult(
                status=CheckStatus.FAILED,
                mount_point=mount_point,
                is_mounted=False,
                mount_info={},
                check_time=datetime.now(),
                error=str(e)
            )
            
            self._save_mount_history(mount_point, result)
            return result
    
    def _get_mount_info(self, mount_point: str) -> Optional[Dict[str, Any]]:
        """获取挂载信息"""
        try:
            # 读取 /proc/mounts 文件
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[1] == mount_point:
                        return {
                            'device': parts[0],
                            'mount_point': parts[1],
                            'filesystem': parts[2],
                            'options': parts[3] if len(parts) > 3 else '',
                            'dump': parts[4] if len(parts) > 4 else '0',
                            'pass': parts[5] if len(parts) > 5 else '0'
                        }
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取挂载信息失败: {e}")
            return None
    
    def _test_mount_access(self, mount_point: str) -> bool:
        """测试挂载点访问"""
        try:
            # 尝试列出目录内容
            os.listdir(mount_point)
            
            # 尝试创建临时文件
            test_file = os.path.join(mount_point, f'.easysync_test_{int(time.time())}')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.unlink(test_file)
                return True
            except (OSError, IOError):
                # 如果无法写入，至少检查是否可读
                return os.access(mount_point, os.R_OK)
                
        except Exception as e:
            self.logger.debug(f"挂载点访问测试失败: {e}")
            return False
    
    def _save_mount_history(self, mount_point: str, result: MountResult):
        """保存挂载检查历史"""
        with self.history_lock:
            if mount_point not in self.mount_history:
                self.mount_history[mount_point] = []
            
            self.mount_history[mount_point].append(result)
            
            # 限制历史记录数量
            max_history = self.config.get('mount_check', {}).get('max_history', 100)
            if len(self.mount_history[mount_point]) > max_history:
                self.mount_history[mount_point].pop(0)
    
    def get_mount_history(self, mount_point: str) -> List[MountResult]:
        """获取挂载检查历史"""
        with self.history_lock:
            return self.mount_history.get(mount_point, [])
    
    def mount_storage(self, mount_point: str, storage_config: Dict[str, Any]) -> MountResult:
        """挂载存储"""
        try:
            # 确保挂载点目录存在
            os.makedirs(mount_point, exist_ok=True)
            
            # 根据存储类型执行挂载
            storage_type = storage_config.get('type', '').lower()
            
            if storage_type in ['nas', 'nfs']:
                return self._mount_nfs(mount_point, storage_config)
            elif storage_type == 'smb':
                return self._mount_smb(mount_point, storage_config)
            else:
                return MountResult(
                    status=CheckStatus.FAILED,
                    mount_point=mount_point,
                    is_mounted=False,
                    mount_info={},
                    check_time=datetime.now(),
                    error=f"不支持的存储类型: {storage_type}"
                )
                
        except Exception as e:
            self.logger.error(f"挂载存储失败: {e}")
            return MountResult(
                status=CheckStatus.FAILED,
                mount_point=mount_point,
                is_mounted=False,
                mount_info={},
                check_time=datetime.now(),
                error=str(e)
            )
    
    def _mount_nfs(self, mount_point: str, storage_config: Dict[str, Any]) -> MountResult:
        """挂载NFS存储"""
        try:
            # 直接从storage_config获取config
            config = storage_config.get('config', {})
            
            host = config.get('host') or config.get('server')  # 兼容两种字段名
            share_path = config.get('share_path') or config.get('path')  # 兼容两种字段名
            options = config.get('options', '')
            version = config.get('version', '3')
            
            if not host or not share_path:
                return MountResult(
                    status=CheckStatus.FAILED,
                    mount_point=mount_point,
                    is_mounted=False,
                    mount_info={},
                    check_time=datetime.now(),
                    error="缺少NFS配置信息：需要server/host和path/share_path字段"
                )
            
            # 构建挂载命令
            source = f"{host}:{share_path}"
            mount_cmd = ['mount']
            
            # 添加选项
            if options:
                mount_cmd.extend(['-o', options])
            
            # 添加版本
            if version:
                mount_cmd.extend(['-o', f'nfsvers={version}'])
            
            mount_cmd.extend([source, mount_point])
            
            # 执行挂载
            self.logger.info(f"执行NFS挂载: {' '.join(mount_cmd)}")
            result = subprocess.run(mount_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # 验证挂载结果
                verify_result = self.check_mount_status(mount_point)
                if verify_result.is_mounted:
                    return MountResult(
                        status=CheckStatus.SUCCESS,
                        mount_point=mount_point,
                        is_mounted=True,
                        mount_info=verify_result.mount_info,
                        check_time=datetime.now()
                    )
                else:
                    return MountResult(
                        status=CheckStatus.FAILED,
                        mount_point=mount_point,
                        is_mounted=False,
                        mount_info={},
                        check_time=datetime.now(),
                        error="挂载成功但验证失败"
                    )
            else:
                return MountResult(
                    status=CheckStatus.FAILED,
                    mount_point=mount_point,
                    is_mounted=False,
                    mount_info={},
                    check_time=datetime.now(),
                    error=f"挂载失败: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return MountResult(
                status=CheckStatus.TIMEOUT,
                mount_point=mount_point,
                is_mounted=False,
                mount_info={},
                check_time=datetime.now(),
                error="挂载操作超时"
            )
        except Exception as e:
            return MountResult(
                status=CheckStatus.FAILED,
                mount_point=mount_point,
                is_mounted=False,
                mount_info={},
                check_time=datetime.now(),
                error=str(e)
            )
    
    def _mount_smb(self, mount_point: str, storage_config: Dict[str, Any]) -> MountResult:
        """挂载SMB存储"""
        try:
            # 直接从storage_config获取config
            config = storage_config.get('config', {})
            
            host = config.get('host') or config.get('server')  # 兼容两种字段名
            share_path = config.get('share_path') or config.get('path')  # 兼容两种字段名
            username = config.get('username', '')
            password = config.get('password', '')
            workgroup = config.get('workgroup', '')
            options = config.get('options', '')
            
            if not host or not share_path:
                return MountResult(
                    status=CheckStatus.FAILED,
                    mount_point=mount_point,
                    is_mounted=False,
                    mount_info={},
                    check_time=datetime.now(),
                    error="缺少SMB配置信息：server和path字段"
                )
            
            # 构建挂载命令
            source = f"//{host}/{share_path}"
            mount_cmd = ['mount', '-t', 'cifs']
            
            # 构建选项字符串
            mount_options = []
            if username:
                mount_options.append(f"username={username}")
            if password:
                mount_options.append(f"password={password}")
            if workgroup:
                mount_options.append(f"domain={workgroup}")
            if options:
                mount_options.append(options)
            
            if mount_options:
                mount_cmd.extend(['-o', ','.join(mount_options)])
            
            mount_cmd.extend([source, mount_point])
            
            # 执行挂载
            self.logger.info(f"执行SMB挂载: {' '.join(mount_cmd)}")
            result = subprocess.run(mount_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # 验证挂载结果
                verify_result = self.check_mount_status(mount_point)
                if verify_result.is_mounted:
                    return MountResult(
                        status=CheckStatus.SUCCESS,
                        mount_point=mount_point,
                        is_mounted=True,
                        mount_info=verify_result.mount_info,
                        check_time=datetime.now()
                    )
                else:
                    return MountResult(
                        status=CheckStatus.FAILED,
                        mount_point=mount_point,
                        is_mounted=False,
                        mount_info={},
                        check_time=datetime.now(),
                        error="挂载成功但验证失败"
                    )
            else:
                return MountResult(
                    status=CheckStatus.FAILED,
                    mount_point=mount_point,
                    is_mounted=False,
                    mount_info={},
                    check_time=datetime.now(),
                    error=f"挂载失败: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return MountResult(
                status=CheckStatus.TIMEOUT,
                mount_point=mount_point,
                is_mounted=False,
                mount_info={},
                check_time=datetime.now(),
                error="挂载操作超时"
            )
        except Exception as e:
            return MountResult(
                status=CheckStatus.FAILED,
                mount_point=mount_point,
                is_mounted=False,
                mount_info={},
                check_time=datetime.now(),
                error=str(e)
            )
    
    def get_all_mounts(self) -> List[Dict[str, Any]]:
        """获取所有挂载点信息"""
        try:
            mounts = []
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        mounts.append({
                            'device': parts[0],
                            'mount_point': parts[1],
                            'filesystem': parts[2],
                            'options': parts[3] if len(parts) > 3 else '',
                            'dump': parts[4] if len(parts) > 4 else '0',
                            'pass': parts[5] if len(parts) > 5 else '0'
                        })
            return mounts
            
        except Exception as e:
            self.logger.error(f"获取挂载信息失败: {e}")
            return []