import os
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime

class LogManager:
    """日志管理类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('LogManager')
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        # 创建日志目录
        log_dir = self.config.get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.get('log_level', 'INFO'))
        
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        return logging.getLogger(name)
        
    def log_task_event(self, task_id: str, event_type: str, data: Dict[str, Any]):
        """记录任务事件
        
        Args:
            task_id: 任务ID
            event_type: 事件类型
            data: 事件数据
        """
        try:
            logger = self.get_logger(f'task.{task_id}')
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': event_type,
                'data': data
            }
            logger.info(json.dumps(event))
        except Exception as e:
            self.logger.error(f"Error logging task event: {e}")
            
    def log_error(self, task_id: str, error: Exception, context: Dict[str, Any] = None):
        """记录错误
        
        Args:
            task_id: 任务ID
            error: 错误对象
            context: 上下文信息
        """
        try:
            logger = self.get_logger(f'task.{task_id}')
            error_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {}
            }
            logger.error(json.dumps(error_data), exc_info=True)
        except Exception as e:
            self.logger.error(f"Error logging error: {e}")
            
    def cleanup_old_logs(self, max_age_days: int = 30):
        """清理旧日志
        
        Args:
            max_age_days: 最大保留天数
        """
        try:
            log_dir = self.config.get('log_dir', 'logs')
            now = datetime.utcnow()
            
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age_days = (now - file_time).days
                    
                    if age_days > max_age_days:
                        os.remove(file_path)
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")
            raise 