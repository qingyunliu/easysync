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
        
    def _estimate_progress_by_time(self):
        """基于时间估算进度"""
        if not self.start_time:
            return 0
            
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        
        # 基于经验值估算：
        # - 前10秒：0-20%
        # - 10-60秒：20-60%  
        # - 60秒后：60-90%
        # - 最后阶段：90-100%
        
        if elapsed < 10:
            return min(int((elapsed / 10) * 20), 20)
        elif elapsed < 60:
            return min(20 + int(((elapsed - 10) / 50) * 40), 60)
        elif elapsed < 300:  # 5分钟
            return min(60 + int(((elapsed - 60) / 240) * 30), 90)
        else:
            return min(90 + int(((elapsed - 300) / 300) * 10), 99)
    
    def update_rsync_progress(self, line: str):
        """更新rsync进度"""
        try:
            line = line.strip()
            self.logger.debug(f"Parsing rsync line: {line}")
            
            # 解析rsync输出
            if 'total size is' in line:
                # 总大小信息 - 格式: "total size is 1,234,567  speedup is 1.23"
                match = re.search(r'total size is (\d+(?:,\d+)*)', line)
                if match:
                    size_str = match.group(1).replace(',', '')
                    self.total_size = int(size_str)
                    self.logger.debug(f"Total size: {self.total_size}")
                    
            elif 'sending incremental file list' in line:
                # 开始传输文件列表
                self.transferred_files = 0
                self.logger.debug("Starting file list transfer")
                
            elif line and not line.startswith(' ') and not line.endswith('%'):
                # 文件名行 - 这表示一个文件开始传输
                self.transferred_files += 1
                self.logger.debug(f"File transferred: {line} (total: {self.transferred_files})")
                
                # 基于文件数量估算进度
                if self.total_files > 0:
                    self.current_progress = min(int((self.transferred_files / self.total_files) * 100), 99)
                else:
                    # 如果没有总文件数，使用时间估算
                    self.current_progress = self._estimate_progress_by_time()
                
                # 更新状态
                self._update_status()
                
            elif '%' in line and 'speedup' not in line:
                # 单个文件的进度信息 - 格式: "1,234 100%    1.23MB/s    0:00:01"
                match = re.search(r'(\d+(?:,\d+)*)\s+(\d+)%\s+(\d+(?:\.\d+)?[kMGT]?B/s)', line)
                if match:
                    transferred = int(match.group(1).replace(',', ''))
                    percentage = int(match.group(2))
                    speed = match.group(3)
                    
                    # 更新传输大小
                    self.transferred_size += transferred
                    
                    # 如果是100%，说明这个文件传输完成
                    if percentage == 100:
                        self.transferred_files += 1
                        
                        # 基于文件数量估算总体进度
                        if self.total_files > 0:
                            self.current_progress = min(int((self.transferred_files / self.total_files) * 100), 99)
                        elif self.total_size > 0:
                            # 基于传输大小估算
                            self.current_progress = min(int((self.transferred_size / self.total_size) * 100), 99)
                        else:
                            # 使用时间估算
                            self.current_progress = self._estimate_progress_by_time()
                        
                        self.logger.debug(f"File completed: {self.transferred_files} files, {self.transferred_size} bytes")
                        
                        # 更新状态
                        self._update_status()
                        
            # 解析 --info=progress2 输出（大数据量推荐）
            elif re.match(r'^\d+(?:,\d+)*\s+\d+%\s+\d+(?:\.\d+)?[kMGT]?B/s\s+\d+:\d+:\d+', line):
                # 格式: "1,234,567,890  45%   10.45MB/s    0:03:24 (xfr#34, to-chk=900/1000)"
                match = re.search(r'(\d+(?:,\d+)*)\s+(\d+)%\s+(\d+(?:\.\d+)?[kMGT]?B/s)\s+(\d+:\d+:\d+)(?:\s+\(xfr#(\d+),\s+to-chk=(\d+)/(\d+)\))?', line)
                if match:
                    transferred_bytes = int(match.group(1).replace(',', ''))
                    percentage = int(match.group(2))
                    speed = match.group(3)
                    eta = match.group(4)
                    
                    # 更新传输大小和进度
                    self.transferred_size = transferred_bytes
                    self.current_progress = percentage
                    
                    # 如果有文件传输信息
                    if match.group(5) and match.group(6) and match.group(7):
                        transferred_files = int(match.group(5))
                        remaining_files = int(match.group(6))
                        total_files = int(match.group(7))
                        self.transferred_files = transferred_files
                        self.total_files = total_files
                    
                    # 对于大数据量，减少日志输出频率
                    if self.current_progress % 5 == 0 or self.current_progress == 100:  # 每5%输出一次
                        self.logger.info(f"Progress2: {percentage}%, {transferred_bytes} bytes, {speed}, ETA: {eta}")
                    else:
                        self.logger.debug(f"Progress2: {percentage}%, {transferred_bytes} bytes, {speed}, ETA: {eta}")
                    
                    # 更新状态
                    self._update_status()
                    
            # 如果没有其他匹配，使用时间估算作为备选
            elif line.strip() and not line.startswith('sending') and not line.startswith('total'):
                # 任何其他输出行，使用时间估算
                estimated_progress = self._estimate_progress_by_time()
                if estimated_progress > self.current_progress:
                    self.current_progress = estimated_progress
                    self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error parsing rsync progress: {e}")
            
    def update_rclone_progress(self, line: str):
        """更新rclone进度"""
        try:
            self.logger.debug(f"Parsing rclone line: {line.strip()}")
            
            # 解析rclone输出
            if 'Transferred:' in line and ',' in line:
                # 总体进度 - 格式: "Transferred: 41.235M / 5.469 GBytes, 1%, 4.364 MBytes/s, ETA 21m13s"
                # 或者: "Transferred: 9 / 1400, 1%"
                
                # 优先解析包含百分比的行（总体进度）
                if '%' in line:
                    # 解析进度百分比
                    match = re.search(r'(\d+)%', line)
                    if match:
                        new_progress = int(match.group(1))
                        # 只有当进度增加时才更新，避免来回跳动
                        if new_progress >= self.current_progress:
                            self.current_progress = new_progress
                            self.logger.debug(f"Progress: {self.current_progress}%")
                
                # 解析文件计数（只在包含数字/数字格式时）
                match = re.search(r'Transferred:\s+(\d+)\s*/\s*(\d+)', line)
                if match:
                    new_transferred = int(match.group(1))
                    new_total = int(match.group(2))
                    # 只有当文件计数增加时才更新
                    if new_transferred >= self.transferred_files:
                        self.transferred_files = new_transferred
                        self.total_files = new_total
                        self.logger.debug(f"Files: {self.transferred_files}/{self.total_files}")
                
                # 更新状态
                self._update_status()
                
            elif 'Checks:' in line:
                # 检查阶段 - 格式: "Checks: 1/2, 50%"
                match = re.search(r'Checks:\s+(\d+)/(\d+)', line)
                if match:
                    self.transferred_files = int(match.group(1))
                    self.total_files = int(match.group(2))
                    
                match = re.search(r'(\d+)%', line)
                if match:
                    new_progress = int(match.group(1))
                    if new_progress >= self.current_progress:
                        self.current_progress = new_progress
                    
                # 更新状态
                self._update_status()
                
            elif 'Elapsed time:' in line:
                # 完成信息
                self.current_progress = 100
                self._update_status()
                
        except Exception as e:
            self.logger.error(f"Error parsing rclone progress: {e}")
            self.logger.error(f"Line: {line}")
            
    def _update_status(self):
        """更新状态"""
        if not self.callback:
            return
            
        # 构建详细的状态信息
        status_info = {
            'progress': self.current_progress,
            'transferred_files': self.transferred_files,
            'total_files': self.total_files,
            'transferred_size': self.transferred_size,
            'total_size': self.total_size,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_update': datetime.utcnow().isoformat()
        }
        
        # 计算传输速度
        if self.start_time:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            if elapsed > 0 and self.transferred_size > 0:
                speed_bps = self.transferred_size / elapsed
                if speed_bps > 1024 * 1024:
                    status_info['transfer_speed'] = f"{speed_bps / (1024 * 1024):.2f} MB/s"
                elif speed_bps > 1024:
                    status_info['transfer_speed'] = f"{speed_bps / 1024:.2f} KB/s"
                else:
                    status_info['transfer_speed'] = f"{speed_bps:.0f} B/s"
        
        # 计算剩余时间
        if self.current_progress > 0 and self.current_progress < 100:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
            if elapsed > 0:
                total_time = (elapsed / self.current_progress) * 100
                remaining_time = total_time - elapsed
                if remaining_time > 0:
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    status_info['eta'] = f"{minutes:02d}:{seconds:02d}"
        
        # 调用回调函数
        try:
            self.callback(status_info)
        except Exception as e:
            self.logger.error(f"Error in progress callback: {e}")
            
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