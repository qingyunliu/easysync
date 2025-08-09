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
            msg = log_entry.get("msg", "")
            
            # 从 msg 字段解析进度信息
            progress_info = self._parse_rclone_msg(msg)
            
            # 从 stats 字段获取结构化数据
            transferred_bytes = stats.get("bytes", 0)
            speed = stats.get("speed", 0.0)  # bytes per second
            transferred_files = stats.get("transfers", 0)
            
            # 使用从 msg 解析的信息
            percent = progress_info.get('percent', 0)
            total_bytes = progress_info.get('total_bytes', 0)
            total_files = progress_info.get('total_files', 0)
            checked = progress_info.get('checked', 0)
            total_checks = progress_info.get('total_checks', 0)
            eta = progress_info.get('eta', 0)  # 从 msg 解析的 ETA
            
            # 格式化输出
            self._format_and_log_progress(
                percent, transferred_bytes, total_bytes, 
                speed, eta, transferred_files, total_files,
                checked, total_checks
            )
            
            # 记录详细的传输信息
            def format_bytes(num):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if abs(num) < 1024.0:
                        return f"{num:.2f}{unit}"
                    num /= 1024.0
                return f"{num:.2f}PB"
            
            # 格式化 ETA 时间
            def format_eta(seconds):
                if seconds <= 0:
                    return "未知"
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                if hours > 0:
                    return f"{hours}h{minutes}m{secs}s"
                elif minutes > 0:
                    return f"{minutes}m{secs}s"
                else:
                    return f"{secs}s"
            
            self.logger.info(f"Rclone 传输进度: {transferred_files}/{total_files} 文件, {format_bytes(transferred_bytes)}/{format_bytes(total_bytes)}, 速度: {format_bytes(speed)}/s, 进度: {percent:.1f}%, ETA: {format_eta(eta)}")
            
        except json.JSONDecodeError:
            # 如果不是 JSON 格式，尝试解析传统文本格式
            self._parse_legacy_rclone_output(line)
        except Exception as e:
            self.logger.debug(f"解析 rclone 进度失败: {e}")
    
    def update_rsync_progress(self, line: str):
        """更新 rsync 进度 - 解析 rsync 文本输出"""
        try:
            line = line.strip()
            if not line:
                return
            
            self.logger.debug(f"解析 rsync 输出: {line}")
            
            # rsync 进度格式: 3,925,913,472  55%   20.30MB/s    0:03:04 (xfr#936, ir-chk=2478/20438)
            # 正则匹配数字、百分比、速度和时间
            rsync_pattern = r'(\d+(?:,\d+)*)\s+(\d+)%\s+([0-9.]+[kMGT]?B/s)\s+(\d+:\d+:\d+)'
            match = re.search(rsync_pattern, line)
            
            if match:
                transferred_bytes_str = match.group(1).replace(',', '')
                percent = float(match.group(2))
                speed_str = match.group(3)
                eta_str = match.group(4)
                
                # 解析传输字节数
                transferred_bytes = int(transferred_bytes_str)
                
                # 解析速度 (如 "20.30MB/s")
                speed = self._parse_speed_str(speed_str)
                
                # 解析 ETA (如 "0:03:04")
                eta = self._parse_eta_str(eta_str)
                
                # 从 rsync 输出中提取文件信息 (xfr#936, ir-chk=2478/20438)
                transferred_files = 0
                total_files = 0
                
                # 解析传输文件数
                xfr_match = re.search(r'xfr#(\d+)', line)
                if xfr_match:
                    transferred_files = int(xfr_match.group(1))
                
                # 解析总文件数 (ir-chk=2478/20438 中的20438)
                ir_match = re.search(r'ir-chk=\d+/(\d+)', line)
                if ir_match:
                    total_files = int(ir_match.group(1))
                
                # 估算总大小 (基于百分比)
                total_bytes = int(transferred_bytes / (percent / 100)) if percent > 0 else transferred_bytes
                
                # 记录详细进度
                self.logger.info(f"Rsync 传输进度: {transferred_files}/{total_files} 文件, {self._format_bytes(transferred_bytes)}/{self._format_bytes(total_bytes)}, 速度: {self._format_bytes(speed)}/s, 进度: {percent:.1f}%, ETA: {self._format_eta(eta)}")
                
                # 格式化进度信息并调用回调
                self._format_and_log_progress(
                    percent=percent,
                    transferred_bytes=transferred_bytes,
                    total_bytes=total_bytes,
                    speed=speed,
                    eta=eta,
                    transferred_files=transferred_files,
                    total_files=total_files,
                    checked=0,
                    total_checks=0
                )
            else:
                self.logger.debug(f"未能匹配 rsync 进度格式: {line}")
                
        except Exception as e:
            self.logger.debug(f"解析 rsync 进度失败: {e}")
    
    def _parse_speed_str(self, speed_str: str) -> float:
        """解析速度字符串 (如 '20.30MB/s' 或 '0.00kB/s') 为每秒字节数"""
        try:
            # 移除 /s 后缀
            speed_part = speed_str.replace('/s', '')
            
            # 解析数值和单位（支持大小写）
            if speed_part.endswith('KB') or speed_part.endswith('kB'):
                return float(speed_part[:-2]) * 1024
            elif speed_part.endswith('MB') or speed_part.endswith('mB'):
                return float(speed_part[:-2]) * 1024 * 1024
            elif speed_part.endswith('GB') or speed_part.endswith('gB'):
                return float(speed_part[:-2]) * 1024 * 1024 * 1024
            elif speed_part.endswith('TB') or speed_part.endswith('tB'):
                return float(speed_part[:-2]) * 1024 * 1024 * 1024 * 1024
            elif speed_part.endswith('B'):
                return float(speed_part[:-1])
            else:
                return float(speed_part)
        except Exception as e:
            self.logger.debug(f"解析速度失败: {e}")
            return 0.0
    
    def _parse_eta_str(self, eta_str: str) -> int:
        """解析 ETA 字符串 (如 '0:03:04') 为秒数"""
        try:
            parts = eta_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            return 0
        except Exception as e:
            self.logger.debug(f"解析 ETA 失败: {e}")
            return 0
    
    def _format_bytes(self, num: int) -> str:
        """格式化字节数为可读字符串"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num) < 1024.0:
                return f"{num:.2f}{unit}"
            num /= 1024.0
        return f"{num:.2f}PB"
    
    def _format_eta(self, seconds: int) -> str:
        """格式化秒数为时间字符串"""
        if seconds <= 0:
            return "N/A"
        return time.strftime("%H:%M:%S", time.gmtime(seconds))
    
    def _parse_rclone_msg(self, msg: str) -> Dict[str, Any]:
        """解析 rclone msg 字段中的进度信息"""
        try:
            result = {
                'percent': 0,
                'total_bytes': 0,
                'total_files': 0,
                'checked': 0,
                'total_checks': 0
            }
            
            # 解析 "Transferred: 12.000M / 4.586 GBytes, 0%, 1.467 MBytes/s, ETA 53m12s" 格式
            # 这个模式匹配传输大小和总大小
            size_pattern = r'Transferred:\s*([^/]+)\s*/\s*([^,]+),\s*([^%]+)%'
            size_match = re.search(size_pattern, msg)
            if size_match:
                transferred_str = size_match.group(1).strip()
                total_str = size_match.group(2).strip()
                percent_str = size_match.group(3).strip()
                
                # 解析百分比
                try:
                    result['percent'] = float(percent_str)
                except ValueError:
                    pass
                
                # 解析总大小
                result['total_bytes'] = self._parse_size(total_str)
            
            # 解析 "Transferred: 3 / 1174, 0%" 格式
            # 这个模式匹配传输文件数和总文件数
            files_pattern = r'Transferred:\s*(\d+)\s*/\s*(\d+),\s*([^%]+)%'
            files_match = re.search(files_pattern, msg)
            if files_match:
                transferred_files = int(files_match.group(1))
                total_files = int(files_match.group(2))
                files_percent = float(files_match.group(3))
                
                result['total_files'] = total_files
                # 如果文件百分比更准确，使用文件百分比
                if files_percent > 0:
                    result['percent'] = files_percent
            
            # 解析 "Checks: 0 / 0, 0%" 格式
            checks_pattern = r'Checks:\s*(\d+)\s*/\s*(\d+),\s*([^%]+)%'
            checks_match = re.search(checks_pattern, msg)
            if checks_match:
                checked = int(checks_match.group(1))
                total_checks = int(checks_match.group(2))
                
                result['checked'] = checked
                result['total_checks'] = total_checks
            
            # 解析 ETA 信息，如 "ETA 30m49s" 或 "ETA 5m24s"
            eta_pattern = r'ETA\s+([^,\s]+)'
            eta_match = re.search(eta_pattern, msg)
            if eta_match:
                eta_str = eta_match.group(1)
                result['eta'] = self._parse_eta_time(eta_str)
            
            return result
            
        except Exception as e:
            self.logger.debug(f"解析 rclone msg 失败: {e}")
            return {
                'percent': 0,
                'total_bytes': 0,
                'total_files': 0,
                'checked': 0,
                'total_checks': 0
            }
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串，如 '4.586 GBytes' 或 '10.420 G' 转换为字节数"""
        try:
            size_str = size_str.strip()
            
            # 移除 'Bytes' 后缀
            if size_str.endswith('Bytes'):
                size_str = size_str[:-5]
            
            # 解析数字和单位
            if 'GB' in size_str or size_str.endswith(' G'):
                # 处理 'GB' 或 ' G' 格式
                if 'GB' in size_str:
                    number = float(size_str.replace('GB', ''))
                else:
                    number = float(size_str.replace(' G', ''))
                return int(number * 1024 * 1024 * 1024)
            elif 'MB' in size_str or size_str.endswith(' M'):
                # 处理 'MB' 或 ' M' 格式
                if 'MB' in size_str:
                    number = float(size_str.replace('MB', ''))
                else:
                    number = float(size_str.replace(' M', ''))
                return int(number * 1024 * 1024)
            elif 'KB' in size_str or size_str.endswith(' K'):
                # 处理 'KB' 或 ' K' 格式
                if 'KB' in size_str:
                    number = float(size_str.replace('KB', ''))
                else:
                    number = float(size_str.replace(' K', ''))
                return int(number * 1024)
            elif 'B' in size_str:
                number = float(size_str.replace('B', ''))
                return int(number)
            else:
                # 尝试直接解析数字
                return int(float(size_str))
                
        except Exception as e:
            self.logger.debug(f"解析大小字符串失败 '{size_str}': {e}")
            return 0
    
    def _parse_eta_time(self, eta_str: str) -> int:
        """解析 ETA 时间字符串，如 '30m49s' 转换为秒数"""
        try:
            eta_str = eta_str.strip()
            total_seconds = 0
            
            # 解析小时 (h)
            if 'h' in eta_str:
                hours_match = re.search(r'(\d+)h', eta_str)
                if hours_match:
                    hours = int(hours_match.group(1))
                    total_seconds += hours * 3600
                    eta_str = eta_str.replace(f'{hours}h', '')
            
            # 解析分钟 (m)
            if 'm' in eta_str:
                minutes_match = re.search(r'(\d+)m', eta_str)
                if minutes_match:
                    minutes = int(minutes_match.group(1))
                    total_seconds += minutes * 60
                    eta_str = eta_str.replace(f'{minutes}m', '')
            
            # 解析秒 (s)
            if 's' in eta_str:
                seconds_match = re.search(r'(\d+)s', eta_str)
                if seconds_match:
                    seconds = int(seconds_match.group(1))
                    total_seconds += seconds
            
            return total_seconds
            
        except Exception as e:
            self.logger.debug(f"解析 ETA 时间失败 '{eta_str}': {e}")
            return 0
    
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