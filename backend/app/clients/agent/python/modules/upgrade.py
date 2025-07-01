import os
import sys
import json
import shutil
import logging
import tempfile
import requests
import platform
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class UpgradeManager:
    def __init__(self, sio, user_id: str, client_id: str, current_version: str, 
                 upgrade_url: str, backup_dir: str = "backups"):
        self.sio = sio
        self.user_id = user_id,
        self.client_id = client_id
        self.current_version = current_version
        self.upgrade_url = upgrade_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def check_upgrade(self) -> Optional[Dict[str, Any]]:
        """检查是否有新版本"""
        try:
            response = requests.get(f"{self.upgrade_url}/version")
            response.raise_for_status()
            latest_version = response.json()
            
            if self._compare_versions(latest_version['version'], self.current_version) > 0:
                logger.info(f"发现新版本: {latest_version['version']}")
                return latest_version
            else:
                logger.info("当前已是最新版本")
                return None
                
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return None
            
    def download_upgrade(self, version: str) -> Optional[Path]:
        """下载升级包"""
        try:
            # 获取系统信息
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            # 构建下载URL
            download_url = f"{self.upgrade_url}/download/{version}/{system}/{machine}"
            
            # 创建临时目录
            temp_dir = Path(tempfile.mkdtemp())
            download_path = temp_dir / f"agent-{version}.zip"
            
            # 下载文件
            logger.info(f"正在下载升级包: {download_url}")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"升级包下载完成: {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"下载升级包失败: {e}")
            return None
            
    def backup_current(self) -> Optional[Path]:
        """备份当前版本"""
        try:
            # 创建备份目录
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"agent_{self.current_version}_{backup_time}"
            
            # 获取当前程序目录
            current_dir = Path(os.path.dirname(os.path.dirname(__file__)))
            
            # 复制文件
            logger.info(f"正在备份当前版本到: {backup_path}")
            shutil.copytree(current_dir, backup_path)
            
            logger.info("备份完成")
            return backup_path
            
        except Exception as e:
            logger.error(f"备份当前版本失败: {e}")
            return None
            
    def apply_upgrade(self, upgrade_path: Path) -> bool:
        """应用升级"""
        try:
            # 获取当前程序目录
            current_dir = Path(os.path.dirname(os.path.dirname(__file__)))
            
            # 解压升级包
            logger.info("正在解压升级包...")
            temp_dir = Path(tempfile.mkdtemp())
            shutil.unpack_archive(upgrade_path, temp_dir)
            
            # 停止当前进程
            logger.info("正在停止当前进程...")
            self.sio.disconnect()
            
            # 替换文件
            logger.info("正在替换文件...")
            for item in temp_dir.iterdir():
                target = current_dir / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(item), str(current_dir))
                
            logger.info("升级文件替换完成")
            return True
            
        except Exception as e:
            logger.error(f"应用升级失败: {e}")
            return False
            
    def rollback(self, backup_path: Path) -> bool:
        """回滚到备份版本"""
        try:
            # 获取当前程序目录
            current_dir = Path(os.path.dirname(os.path.dirname(__file__)))
            
            # 停止当前进程
            logger.info("正在停止当前进程...")
            self.sio.disconnect()
            
            # 恢复备份
            logger.info(f"正在恢复备份: {backup_path}")
            for item in backup_path.iterdir():
                target = current_dir / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(item), str(current_dir))
                
            logger.info("备份恢复完成")
            return True
            
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return False
            
    def restart(self):
        """重启客户端"""
        try:
            # 获取当前程序路径
            current_path = Path(sys.argv[0])
            
            # 启动新进程
            logger.info("正在重启客户端...")
            subprocess.Popen([sys.executable, str(current_path)])
            
            # 退出当前进程
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"重启客户端失败: {e}")
            
    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号"""
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_part = v1_parts[i] if i < len(v1_parts) else 0
            v2_part = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1_part > v2_part:
                return 1
            elif v1_part < v2_part:
                return -1
                
        return 0 