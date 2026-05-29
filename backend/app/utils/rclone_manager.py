"""
rclone 管理模块

负责 rclone 安装包的管理和远程安装
"""
import os
import logging
from typing import Optional, Tuple
from backend.app.utils.ssh_utils import SSHClient
from backend.app.models import Node

logger = logging.getLogger(__name__)

# rclone 配置
RCLONE_BASE_DIR = '/opt/easysync/rclone'
RCLONE_CURRENT_VERSION = 'v1.68.0'
RCLONE_PACKAGE_NAME = f'rclone-{RCLONE_CURRENT_VERSION}-linux-amd64.zip'
RCLONE_PACKAGE_PATH = os.path.join(RCLONE_BASE_DIR, RCLONE_PACKAGE_NAME)
RCLONE_EXTRACTED_DIR = os.path.join(RCLONE_BASE_DIR, f'rclone-{RCLONE_CURRENT_VERSION}-linux-amd64')
RCLONE_BINARY_PATH = os.path.join(RCLONE_EXTRACTED_DIR, 'rclone')
RCLONE_REMOTE_INSTALL_PATH = '/usr/bin/rclone'


class RcloneManager:
    """rclone 管理类"""
    
    def __init__(self):
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        try:
            os.makedirs(RCLONE_BASE_DIR, exist_ok=True)
            logger.info(f"rclone 目录已准备: {RCLONE_BASE_DIR}")
        except Exception as e:
            logger.error(f"创建 rclone 目录失败: {e}")
            raise
    
    def is_package_available(self) -> bool:
        """检查 rclone 安装包是否可用"""
        return os.path.exists(RCLONE_PACKAGE_PATH)
    
    def get_package_info(self) -> dict:
        """获取 rclone 包信息"""
        return {
            'version': RCLONE_CURRENT_VERSION,
            'package_path': RCLONE_PACKAGE_PATH,
            'package_exists': self.is_package_available(),
            'extracted_dir': RCLONE_EXTRACTED_DIR,
            'binary_path': RCLONE_BINARY_PATH
        }
    
    def install_on_remote(self, node: Node) -> Tuple[bool, str]:
        """
        在远程节点上安装 rclone
        
        Args:
            node: 节点对象
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 检查本地安装包
            if not self.is_package_available():
                error_msg = f"rclone 安装包不存在: {RCLONE_PACKAGE_PATH}"
                logger.error(error_msg)
                return False, error_msg
            
            logger.info(f"开始为节点 {node.name} ({node.ipaddress}) 安装 rclone")
            
            with SSHClient(node=node) as ssh:
                # 1. 检查远程 rclone 是否已安装
                stdout, stderr, exit_code = ssh.execute_command('which rclone')
                rclone_installed = exit_code == 0
                
                if rclone_installed:
                    # 检查版本
                    stdout, stderr, exit_code = ssh.execute_command('rclone version')
                    current_version = stdout.strip() if stdout.strip() else 'unknown'
                    logger.info(f"远程节点已安装 rclone: {current_version}")
                    
                    # 如果版本相同，跳过安装
                    if RCLONE_CURRENT_VERSION in current_version:
                        msg = f"rclone {RCLONE_CURRENT_VERSION} 已安装，跳过"
                        logger.info(msg)
                        return True, msg
                
                # 2. 上传安装包
                remote_package_path = f'/tmp/{RCLONE_PACKAGE_NAME}'
                logger.info(f"上传 rclone 安装包到 {remote_package_path}")
                ssh.upload_file(RCLONE_PACKAGE_PATH, remote_package_path)
                logger.info("安装包上传成功")
                
                # 3. 解压安装包
                logger.info("解压安装包")
                extract_cmd = f"cd /tmp && python3 -m zipfile -e {RCLONE_PACKAGE_NAME} /tmp/"
                stdout, stderr, exit_code = ssh.execute_command(extract_cmd)
                
                if exit_code != 0:
                    error_msg = f"解压失败: {stderr}"
                    logger.error(error_msg)
                    return False, error_msg
                
                logger.info("安装包解压成功")
                
                # 4. 备份旧版本（如果存在）
                if rclone_installed:
                    logger.info("备份旧版本 rclone")
                    backup_cmd = f"sudo cp {RCLONE_REMOTE_INSTALL_PATH} {RCLONE_REMOTE_INSTALL_PATH}.backup 2>/dev/null || true"
                    ssh.execute_command(backup_cmd)
                
                # 5. 安装新版本
                logger.info("安装新版本 rclone")
                install_cmd = f"sudo cp /tmp/rclone-{RCLONE_CURRENT_VERSION}-linux-amd64/rclone {RCLONE_REMOTE_INSTALL_PATH} && sudo chmod +x {RCLONE_REMOTE_INSTALL_PATH}"
                stdout, stderr, exit_code = ssh.execute_command(install_cmd)
                
                if exit_code != 0:
                    error_msg = f"安装失败: {stderr}"
                    logger.error(error_msg)
                    return False, error_msg
                
                logger.info("rclone 安装成功")
                
                # 6. 验证安装
                stdout, stderr, exit_code = ssh.execute_command('rclone version')
                if exit_code == 0:
                    installed_version = stdout.strip()
                    logger.info(f"rclone 版本验证成功: {installed_version}")
                    
                    # 7. 清理临时文件
                    cleanup_cmd = f"rm -f /tmp/{RCLONE_PACKAGE_NAME} && rm -rf /tmp/rclone-{RCLONE_CURRENT_VERSION}-linux-amd64"
                    ssh.execute_command(cleanup_cmd)
                    logger.info("临时文件清理完成")
                    
                    msg = f"rclone {installed_version} 安装成功"
                    logger.info(msg)
                    return True, msg
                else:
                    error_msg = f"rclone 版本验证失败: {stderr}"
                    logger.error(error_msg)
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"安装 rclone 时出错: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def check_remote_rclone(self, node: Node) -> Tuple[bool, str, Optional[str]]:
        """
        检查远程节点上的 rclone 状态
        
        Args:
            node: 节点对象
            
        Returns:
            Tuple[bool, str, Optional[str]]: (是否安装, 消息, 版本)
        """
        try:
            with SSHClient(node=node) as ssh:
                stdout, stderr, exit_code = ssh.execute_command('which rclone')
                
                if exit_code != 0:
                    return False, "rclone 未安装", None
                
                stdout, stderr, exit_code = ssh.execute_command('rclone version')
                if exit_code == 0:
                    version = stdout.strip()
                    return True, f"rclone 已安装: {version}", version
                else:
                    return True, "rclone 已安装但无法获取版本", None
                    
        except Exception as e:
            error_msg = f"检查 rclone 时出错: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None


def get_rclone_manager() -> RcloneManager:
    """获取 rclone 管理器单例"""
    if not hasattr(get_rclone_manager, '_instance'):
        get_rclone_manager._instance = RcloneManager()
    return get_rclone_manager._instance