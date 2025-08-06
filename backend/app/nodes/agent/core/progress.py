import re
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from ..utils.logger import get_log_manager

class ProgressMonitor:
    """进度监控类"""
    
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('ProgressMonitor')
        self.callback = callback
        self.current_progress = 0
        self.total_files = 0
        self.transferred_files = 0
        self.total_size = 0
        self.transferred_size = 0
        self.start_time = None
        self.last_update = None
        
    def start(self):
        """开始监控"""
        self.start_time = datetime.utcnow()
        self.last_update = self.start_time
        self.current_progress = 0
        self.total_files = 0
        self.transferred_files = 0
        self.total_size = 0
        self.transferred_size = 0
        
    def update_rsync_progress(self, line: str):
        """更新rsync进度"""
        try:
            # 解析rsync输出
            if 'total size is' in line:
                # 总大小信息
                match = re.search(r'total size is (\d+)', line)
                if match:
                    self.total_size = int(match.group(1))
            elif '%' in line:
                # 进度信息
                match = re.search(r'(\d+)%', line)
                if match:
                    self.current_progress = int(match.group(1))
                    
                # 文件计数
                match = re.search(r'(\d+)/(\d+)', line)
                if match:
                    self.transferred_files = int(match.group(1))
                    self.total_files = int(match.group(2))
                    
                # 更新状态
                self._update_status()
                
        except Exception as e:
            self.logger.error(f"Error parsing rsync progress: {e}")
            
    def update_rclone_progress(self, line: str):
        """更新rclone进度"""
        try:
            # 解析rclone输出
            if 'Transferred:' in line:
                # 传输信息
                match = re.search(r'Transferred:\s+(\d+)/(\d+)', line)
                if match:
                    self.transferred_files = int(match.group(1))
                    self.total_files = int(match.group(2))
                    
                match = re.search(r'(\d+)%', line)
                if match:
                    self.current_progress = int(match.group(1))
                    
                # 更新状态
                self._update_status()
                
        except Exception as e:
            self.logger.error(f"Error parsing rclone progress: {e}")
            
    def _update_status(self):
        """更新状态"""
        now = datetime.utcnow()
        if (now - self.last_update).total_seconds() >= 1:  # 每秒更新一次
            status = {
                'progress': self.current_progress,
                'total_files': self.total_files,
                'transferred_files': self.transferred_files,
                'total_size': self.total_size,
                'transferred_size': self.transferred_size,
                'elapsed_time': (now - self.start_time).total_seconds(),
                'timestamp': now.isoformat()
            }
            
            if self.callback:
                self.callback(status)
                
            self.last_update = now
            
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'progress': self.current_progress,
            'total_files': self.total_files,
            'transferred_files': self.transferred_files,
            'total_size': self.total_size,
            'transferred_size': self.transferred_size,
            'elapsed_time': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        } 