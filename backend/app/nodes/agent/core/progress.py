#!/usr/bin/env python3
"""
任务进度监控器 - 使用 rclone JSON 日志解析
"""

import threading
import time
import json
import re
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from ..utils.logger import get_log_manager

class ProgressType(Enum):
    """进度类型枚举"""
    OVERALL = "overall"       # 整体进度
    FILE = "file"            # 单个文件进度
    NETWORK = "network"      # 网络传输进度
    MOUNT = "mount"          # 挂载进度
    VERIFICATION = "verification"  # 验证进度

@dataclass
class FileProgress:
    """文件进度信息"""
    file_path: str
    size: int
    transferred: int
    speed: float
    eta: Optional[float] = None
    status: str = "transferring"

@dataclass
class NetworkProgress:
    """网络传输进度"""
    bytes_sent: int
    bytes_received: int
    send_rate: float
    receive_rate: float
    connection_count: int
    latency: float

@dataclass
class TaskProgress:
    """任务进度信息"""
    task_id: str
    progress_type: ProgressType
    percentage: float
    current_step: str
    total_steps: int
    current_step_index: int
    
    # 文件相关
    files_total: int = 0
    files_completed: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    
    # 大小相关
    total_size: int = 0
    transferred_size: int = 0
    
    # 速度相关
    transfer_speed: float = 0.0
    average_speed: float = 0.0
    
    # 时间相关
    start_time: Optional[datetime] = None
    eta: Optional[float] = None
    
    # 详细信息
    current_file: Optional[FileProgress] = None
    network_info: Optional[NetworkProgress] = None
    error_count: int = 0
    warning_count: int = 0
    
    # 自定义数据
    custom_data: Dict[str, Any] = field(default_factory=dict)

class ProgressMonitor:
    """进度监控器 - 使用 rclone JSON 日志解析"""
    
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.callback = callback
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('ProgressMonitor')
        
        # 进度数据存储
        self.task_progress: Dict[str, TaskProgress] = {}
        self.progress_lock = threading.Lock()
        
        # 配置参数
        self.report_interval = 5  # 5秒上报一次
        self.detailed_logging = True
        self.max_history_size = 100
        
        # 进度历史记录
        self.progress_history: Dict[str, List[TaskProgress]] = {}
        
        # 回调函数
        self.progress_callbacks: List[Callable[[TaskProgress], None]] = []
        
        # 启动上报线程
        self.report_thread = threading.Thread(target=self._report_progress_loop, daemon=True)
        self.report_thread.start()
    
    def start(self):
        """启动进度监控"""
        self.logger.info("进度监控器已启动")
    
    def stop(self):
        """停止进度监控"""
        self.logger.info("进度监控器已停止")
    
    def update_rclone_progress(self, line: str):
        """更新 rclone 进度 - 使用 JSON 日志解析"""
        try:
            # 尝试解析 JSON 日志
            log_entry = json.loads(line.strip())
            
            # 检查是否是统计信息
            if "stats" not in log_entry:
                return
            
            stats = log_entry["stats"]
            
            # 解析基本统计信息
            transferred_bytes = stats.get("bytes", 0)
            total_bytes = stats.get("size", 0)
            percent = (transferred_bytes / total_bytes * 100) if total_bytes else 0
            
            # 解析文件信息
            transfer_stats = stats.get("transfer", {})
            transferred_files = transfer_stats.get("transferred", 0)
            total_files = transfer_stats.get("total", 0)
            
            # 解析检查信息
            checks = stats.get("checks", {})
            if isinstance(checks, dict):
                checked = checks.get("checked", 0)
                total_checks = checks.get("total", 0)
            elif isinstance(checks, int):
                checked = checks
                total_checks = 0
            else:
                checked = total_checks = 0
            
            # 解析速度和ETA
            speed = stats.get("speed", 0.0)  # bytes per second
            eta = stats.get("eta", 0)  # seconds
            
            # 格式化输出
            self._format_and_log_progress(
                percent, transferred_bytes, total_bytes, 
                speed, eta, transferred_files, total_files,
                checked, total_checks
            )
            
        except json.JSONDecodeError:
            # 如果不是 JSON 格式，尝试解析传统文本格式
            self._parse_legacy_rclone_output(line)
        except Exception as e:
            self.logger.debug(f"解析 rclone 进度失败: {e}")
    
    def _parse_legacy_rclone_output(self, line: str):
        """解析传统的 rclone 文本输出"""
        try:
            # 解析 "Transferred: 71 / 3350, 2%" 格式
            if "Transferred:" in line and "Files:" in line:
                # 提取文件数量信息
                files_match = re.search(r'(\d+)\s*/\s*(\d+)', line)
                if files_match:
                    transferred_files = int(files_match.group(1))
                    total_files = int(files_match.group(2))
                    
                    # 计算百分比
                    percent = (transferred_files / total_files * 100) if total_files else 0
                    
                    self.logger.debug(f"Files: {transferred_files}/{total_files}")
                    
                    # 触发回调
                    if self.callback:
                        self.callback({
                            'progress': percent,
                            'transferred_files': transferred_files,
                            'total_files': total_files,
                            'transferred_size': 0,
                            'total_size': 0,
                            'transfer_speed': '',
                            'eta': '',
                            'current_file': '',
                            'current_phase': 'transferring',
                            'last_update': datetime.now().isoformat()
                        })
            
            # 解析 "Transferred: 287.800M / 13.045 GBytes, 2%, 4.012 MBytes/s, ETA 54m17s" 格式
            elif "Transferred:" in line and "ETA" in line:
                # 这里可以添加更详细的解析逻辑
                self.logger.debug(f"Parsing rclone line: {line.strip()}")
                
        except Exception as e:
            self.logger.debug(f"解析传统 rclone 输出失败: {e}")
    
    def _format_and_log_progress(self, percent: float, transferred_bytes: int, total_bytes: int,
                                speed: float, eta: int, transferred_files: int, total_files: int,
                                checked: int, total_checks: int):
        """格式化并记录进度信息"""
        
        def format_bytes(num):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if abs(num) < 1024.0:
                    return f"{num:.2f}{unit}"
                num /= 1024.0
            return f"{num:.2f}PB"
        
        # 格式化输出
        speed_fmt = format_bytes(speed) + "/s" if speed > 0 else "0B/s"
        eta_fmt = time.strftime("%H:%M:%S", time.gmtime(eta)) if eta > 0 else "N/A"
        
        progress_info = (
            f"[Progress] {percent:.2f}% ({format_bytes(transferred_bytes)} / {format_bytes(total_bytes)}) | "
            f"[Speed] {speed_fmt} | [ETA] {eta_fmt} | [Files] {transferred_files}/{total_files} | "
            f"[Checks] {checked}/{total_checks if total_checks else '?'}"
        )
        
        self.logger.info(progress_info)
        
        # 触发回调
        if self.callback:
            self.callback({
                'progress': percent,
                'transferred_files': transferred_files,
                'total_files': total_files,
                'transferred_size': transferred_bytes,
                'total_size': total_bytes,
                'transfer_speed': speed_fmt,
                'eta': eta_fmt,
                'current_file': '',
                'current_phase': 'transferring',
                'last_update': datetime.now().isoformat()
            })
    
    def start_task_progress(self, task_id: str, total_steps: int, step_names: List[str]) -> TaskProgress:
        """开始任务进度跟踪"""
        with self.progress_lock:
            progress = TaskProgress(
                task_id=task_id,
                progress_type=ProgressType.OVERALL,
                percentage=0.0,
                current_step="开始任务",
                total_steps=total_steps,
                current_step_index=0,
                start_time=datetime.now(),
                custom_data={'step_names': step_names}
            )
            
            self.task_progress[task_id] = progress
            self.progress_history[task_id] = []
            
            self.logger.info(f"开始跟踪任务 {task_id} 的进度，共 {total_steps} 个步骤")
            
            return progress
    
    def update_step_progress(self, task_id: str, step_index: int, step_name: str, 
                           step_percentage: float, details: Dict[str, Any] = None):
        """更新步骤进度"""
        with self.progress_lock:
            if task_id not in self.task_progress:
                self.logger.warning(f"任务 {task_id} 未找到进度信息")
                return
            
            progress = self.task_progress[task_id]
            progress.current_step_index = step_index
            progress.current_step = step_name
            
            # 计算整体进度
            base_progress = (step_index / progress.total_steps) * 100
            step_progress = (step_percentage / 100) * (100 / progress.total_steps)
            progress.percentage = min(base_progress + step_progress, 100.0)
            
            # 更新详细信息
            if details:
                if 'files_total' in details:
                    progress.files_total = details['files_total']
                if 'files_completed' in details:
                    progress.files_completed = details['files_completed']
                if 'total_size' in details:
                    progress.total_size = details['total_size']
                if 'transferred_size' in details:
                    progress.transferred_size = details['transferred_size']
                if 'transfer_speed' in details:
                    progress.transfer_speed = details['transfer_speed']
                if 'error_count' in details:
                    progress.error_count = details['error_count']
            
            # 计算ETA
            if progress.start_time and progress.percentage > 0:
                elapsed = (datetime.now() - progress.start_time).total_seconds()
                if progress.percentage < 100:
                    progress.eta = (elapsed / progress.percentage) * (100 - progress.percentage)
            
            # 保存历史记录
            self._save_progress_history(task_id, progress)
            
            # 调用回调函数
            self._trigger_callbacks(progress)
    
    def update_file_progress(self, task_id: str, file_path: str, file_size: int, 
                           transferred: int, speed: float):
        """更新文件传输进度"""
        with self.progress_lock:
            if task_id not in self.task_progress:
                return
            
            progress = self.task_progress[task_id]
            
            # 更新当前文件信息
            file_progress = FileProgress(
                file_path=file_path,
                size=file_size,
                transferred=transferred,
                speed=speed,
                eta=(file_size - transferred) / speed if speed > 0 else None
            )
            
            progress.current_file = file_progress
            
            # 更新整体传输大小
            if progress.transferred_size > 0:
                progress.transferred_size += transferred
            else:
                progress.transferred_size = transferred
            
            progress.transfer_speed = speed
            
            # 调用回调函数
            self._trigger_callbacks(progress)
    
    def update_network_progress(self, task_id: str, bytes_sent: int, bytes_received: int,
                              send_rate: float, receive_rate: float, connection_count: int = 1,
                              latency: float = 0.0):
        """更新网络传输进度"""
        with self.progress_lock:
            if task_id not in self.task_progress:
                return
            
            progress = self.task_progress[task_id]
            
            network_progress = NetworkProgress(
                bytes_sent=bytes_sent,
                bytes_received=bytes_received,
                send_rate=send_rate,
                receive_rate=receive_rate,
                connection_count=connection_count,
                latency=latency
            )
            
            progress.network_info = network_progress
            
            # 调用回调函数
            self._trigger_callbacks(progress)
    
    def complete_task_progress(self, task_id: str, success: bool = True, error: str = None):
        """完成任务进度"""
        with self.progress_lock:
            if task_id not in self.task_progress:
                return
            
            progress = self.task_progress[task_id]
            progress.percentage = 100.0
            progress.current_step = "完成" if success else "失败"
            
            if not success and error:
                progress.error_count += 1
                if progress.custom_data is None:
                    progress.custom_data = {}
                progress.custom_data['final_error'] = error
            
            self.logger.info(f"任务 {task_id} 进度跟踪完成，成功: {success}")
    
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度"""
        with self.progress_lock:
            return self.task_progress.get(task_id)
    
    def get_progress_history(self, task_id: str) -> List[TaskProgress]:
        """获取进度历史"""
        with self.progress_lock:
            return self.progress_history.get(task_id, [])
    
    def add_progress_callback(self, callback: Callable[[TaskProgress], None]):
        """添加进度回调函数"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[TaskProgress], None]):
        """移除进度回调函数"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def _save_progress_history(self, task_id: str, progress: TaskProgress):
        """保存进度历史"""
        if task_id not in self.progress_history:
            self.progress_history[task_id] = []
        
        # 创建进度快照
        progress_snapshot = TaskProgress(
            task_id=progress.task_id,
            progress_type=progress.progress_type,
            percentage=progress.percentage,
            current_step=progress.current_step,
            total_steps=progress.total_steps,
            current_step_index=progress.current_step_index,
            files_total=progress.files_total,
            files_completed=progress.files_completed,
            total_size=progress.total_size,
            transferred_size=progress.transferred_size,
            transfer_speed=progress.transfer_speed,
            start_time=progress.start_time,
            eta=progress.eta,
            error_count=progress.error_count,
            warning_count=progress.warning_count
        )
        
        self.progress_history[task_id].append(progress_snapshot)
        
        # 限制历史记录数量
        if len(self.progress_history[task_id]) > self.max_history_size:
            self.progress_history[task_id].pop(0)
    
    def _trigger_callbacks(self, progress: TaskProgress):
        """触发回调函数"""
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                self.logger.error(f"进度回调函数执行失败: {e}")
    
    def _report_progress_loop(self):
        """进度上报循环"""
        while True:
            try:
                with self.progress_lock:
                    for task_id, progress in self.task_progress.items():
                        if progress.percentage < 100:  # 只上报未完成的任务
                            self._report_progress_to_server(progress)
                
                time.sleep(self.report_interval)
                
            except Exception as e:
                self.logger.error(f"进度上报循环异常: {e}")
                time.sleep(self.report_interval)
    
    def _report_progress_to_server(self, progress: TaskProgress):
        """向服务器上报进度"""
        try:
            # 构建上报数据
            report_data = {
                'task_id': progress.task_id,
                'progress': progress.percentage,
                'current_step': progress.current_step,
                'step_index': progress.current_step_index,
                'total_steps': progress.total_steps,
                'files_total': progress.files_total,
                'files_completed': progress.files_completed,
                'total_size': progress.total_size,
                'transferred_size': progress.transferred_size,
                'transfer_speed': progress.transfer_speed,
                'eta': progress.eta,
                'error_count': progress.error_count,
                'warning_count': progress.warning_count,
                'timestamp': datetime.now().isoformat()
            }
            
            # 添加当前文件信息
            if progress.current_file:
                report_data['current_file'] = {
                    'path': progress.current_file.file_path,
                    'size': progress.current_file.size,
                    'transferred': progress.current_file.transferred,
                    'speed': progress.current_file.speed,
                    'eta': progress.current_file.eta
                }
            
            # 添加网络信息
            if progress.network_info:
                report_data['network'] = {
                    'bytes_sent': progress.network_info.bytes_sent,
                    'bytes_received': progress.network_info.bytes_received,
                    'send_rate': progress.network_info.send_rate,
                    'receive_rate': progress.network_info.receive_rate,
                    'connection_count': progress.network_info.connection_count,
                    'latency': progress.network_info.latency
                }
            
            if self.detailed_logging:
                self.logger.debug(f"上报任务 {progress.task_id} 进度: {progress.percentage:.1f}%")
                
        except Exception as e:
            self.logger.error(f"上报进度失败: {e}")

class ProgressParser:
    """进度解析器 - 从命令行输出解析进度信息"""
    
    def __init__(self):
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('ProgressParser')
        
        # rsync 进度正则表达式
        self.rsync_progress_pattern = re.compile(
            r'(\d+(?:,\d+)*)\s+(\d+)%\s+(\d+(?:\.\d+)?[kMGT]?B/s)\s+(\d+:\d+:\d+)'
        )
        
        # rclone 进度正则表达式
        self.rclone_progress_pattern = re.compile(
            r'Transferred:\s+(\d+(?:\.\d+)?[kMGT]?B)\s+/\s+(\d+(?:\.\d+)?[kMGT]?B),\s+(\d+)%,\s+(\d+(?:\.\d+)?[kMGT]?B/s),\s+ETA\s+(\d+[dhms]+|\d+:\d+:\d+)'
        )
    
    def parse_rsync_output(self, output: str) -> Dict[str, Any]:
        """解析rsync输出"""
        match = self.rsync_progress_pattern.search(output)
        if match:
            transferred = self._parse_size(match.group(1))
            percentage = int(match.group(2))
            speed = self._parse_speed(match.group(3))
            eta = self._parse_time(match.group(4))
            
            return {
                'transferred_size': transferred,
                'percentage': percentage,
                'transfer_speed': speed,
                'eta': eta
            }
        
        return {}
    
    def parse_rclone_output(self, output: str) -> Dict[str, Any]:
        """解析rclone输出"""
        match = self.rclone_progress_pattern.search(output)
        if match:
            transferred = self._parse_size(match.group(1))
            total_size = self._parse_size(match.group(2))
            percentage = int(match.group(3))
            speed = self._parse_speed(match.group(4))
            eta = self._parse_eta(match.group(5))
            
            return {
                'transferred_size': transferred,
                'total_size': total_size,
                'percentage': percentage,
                'transfer_speed': speed,
                'eta': eta
            }
        
        return {}
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数"""
        size_str = size_str.replace(',', '')
        
        units = {'B': 1, 'kB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        
        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                return int(float(size_str[:-len(unit)]) * multiplier)
        
        return int(size_str)
    
    def _parse_speed(self, speed_str: str) -> float:
        """解析速度字符串为每秒字节数"""
        if speed_str.endswith('B/s'):
            return self._parse_size(speed_str[:-2])
        return 0.0
    
    def _parse_time(self, time_str: str) -> int:
        """解析时间字符串为秒数"""
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        return 0
    
    def _parse_eta(self, eta_str: str) -> int:
        """解析ETA字符串为秒数"""
        if ':' in eta_str:
            return self._parse_time(eta_str)
        
        # 处理如 "1h2m3s" 格式
        total_seconds = 0
        if 'h' in eta_str:
            hours = int(eta_str.split('h')[0])
            total_seconds += hours * 3600
            eta_str = eta_str.split('h')[1]
        if 'm' in eta_str:
            minutes = int(eta_str.split('m')[0])
            total_seconds += minutes * 60
            eta_str = eta_str.split('m')[1]
        if 's' in eta_str:
            seconds = int(eta_str.split('s')[0])
            total_seconds += seconds
        
        return total_seconds