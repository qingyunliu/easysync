import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from ..utils.logger import get_log_manager

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"

class TaskPhase(Enum):
    """任务阶段枚举"""
    CREATED = "created"
    ASSIGNED = "assigned"
    CONFIG_CHECK = "config_check"
    CONNECTIVITY_TEST = "connectivity_test"
    MOUNT_SOURCE = "mount_source"
    MOUNT_COMPLETED = "mount_completed"
    SYNC_STARTED = "sync_started"
    SYNC_PROGRESS = "sync_progress"
    SYNC_COMPLETED = "sync_completed"
    TASK_COMPLETED = "task_completed"
    TASK_CANCELLED = "task_cancelled"
    TASK_PAUSED = "task_paused"
    TASK_TIMEOUT = "task_timeout"
    TASK_FAILED = "task_failed"

class LogLevel(Enum):
    """日志级别枚举"""
    INFO = "info"
    ERROR = "error"
    PROGRESS = "progress"

class TaskLogEntry:
    """任务日志条目"""
    
    def __init__(self, task_id: str, phase: TaskPhase, level: LogLevel, message: str, 
                 details: Optional[Dict[str, Any]] = None):
        self.task_id = task_id
        self.phase = phase
        self.level = level
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'phase': self.phase.value,
            'level': self.level.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskLogEntry':
        """从字典创建对象"""
        return cls(
            task_id=data['task_id'],
            phase=TaskPhase(data['phase']),
            level=LogLevel(data['level']),
            message=data['message'],
            details=data.get('details', {}),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )

class TaskState:
    """任务状态管理"""
    
    def __init__(self, state_dir: str = 'state'):
        self.state_dir = state_dir
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('TaskState')
        self._ensure_state_dir()
        
    def _ensure_state_dir(self):
        """确保状态目录存在"""
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir, exist_ok=True)
            
    def save_state(self, task_id: str, state_data: Dict[str, Any]):
        """保存任务状态"""
        try:
            state_file = os.path.join(self.state_dir, f"{task_id}.json")
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存任务状态失败: {e}")
            
    def load_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载任务状态"""
        try:
            state_file = os.path.join(self.state_dir, f"{task_id}.json")
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"加载任务状态失败: {e}")
        return None
        
    def cleanup_old_states(self, max_age_days: int = 7):
        """清理旧的状态文件"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            for filename in os.listdir(self.state_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.state_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        self.logger.info(f"清理旧状态文件: {filename}")
        except Exception as e:
            self.logger.error(f"清理旧状态文件失败: {e}")

class TaskLogger:
    """任务日志管理器"""
    
    def __init__(self, server_comm=None):
        self.server_comm = server_comm
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('TaskLogger')
        
    def log_task_event(self, task_id: str, phase: TaskPhase, level: LogLevel, 
                      message: str, details: Optional[Dict[str, Any]] = None):
        """记录任务事件"""
        try:
            # 创建日志条目
            log_entry = TaskLogEntry(task_id, phase, level, message, details)
            
            # 记录到本地日志
            self.logger.info(f"Task {task_id} - {phase.value}: {message}")
            
            # 上报到服务器
            if self.server_comm:
                self.server_comm.report_task_log(task_id, log_entry.to_dict())
                
        except Exception as e:
            self.logger.error(f"记录任务事件失败: {e}")
            
    def log_task_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """记录任务进度"""
        try:
            # 构建进度消息
            progress = progress_data.get('progress', 0)
            transferred = progress_data.get('transferred_size', 0)
            total = progress_data.get('total_size', 0)
            speed = progress_data.get('transfer_speed', '')
            eta = progress_data.get('eta', '')
            
            message = f"同步进度: {progress}%"
            if transferred and total:
                message += f" ({self._format_size(transferred)}/{self._format_size(total)})"
            if speed:
                message += f" 速度: {speed}"
            if eta:
                message += f" 剩余时间: {eta}"
                
            # 记录进度事件
            self.log_task_event(
                task_id=task_id,
                phase=TaskPhase.SYNC_PROGRESS,
                level=LogLevel.PROGRESS,
                message=message,
                details=progress_data
            )
            
        except Exception as e:
            self.logger.error(f"记录任务进度失败: {e}")
            
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}" 