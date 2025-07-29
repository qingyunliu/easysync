import os
import json
import logging
import logging.handlers
import traceback
import inspect
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
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 创建文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'agent.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 添加处理器到根日志记录器
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        return logging.getLogger(name)
    
    def get_caller_info(self) -> Dict[str, str]:
        """获取调用者信息
        
        Returns:
            Dict[str, str]: 调用者信息
        """
        try:
            # 获取调用栈
            stack = inspect.stack()
            # 跳过当前函数，获取调用者的信息
            caller_frame = stack[2]
            
            return {
                'module': caller_frame.frame.f_globals.get('__name__', 'unknown'),
                'filename': os.path.basename(caller_frame.filename),
                'lineno': caller_frame.lineno,
                'function': caller_frame.function
            }
        except Exception:
            return {
                'module': 'unknown',
                'filename': 'unknown',
                'lineno': 0,
                'function': 'unknown'
            }
        
    def log_task_event(self, task_id: str, event_type: str, data: Dict[str, Any]):
        """记录任务事件
        
        Args:
            task_id: 任务ID
            event_type: 事件类型
            data: 事件数据
        """
        try:
            logger = self.get_logger(f'task.{task_id}')
            caller_info = self.get_caller_info()
            
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': event_type,
                'data': data,
                'caller': caller_info
            }
            
            # 格式化输出
            logger.info(f"Task Event: {event_type} | Task: {task_id} | Data: {json.dumps(data, ensure_ascii=False)}")
            
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
            caller_info = self.get_caller_info()
            
            # 获取完整的错误堆栈
            stack_trace = traceback.format_exc()
            
            error_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {},
                'caller': caller_info,
                'stack_trace': stack_trace
            }
            
            # 格式化输出
            logger.error(
                f"Task Error: {type(error).__name__} | Task: {task_id} | "
                f"Message: {str(error)} | Context: {json.dumps(context or {}, ensure_ascii=False)}"
            )
            
            # 详细错误信息记录到DEBUG级别
            logger.debug(f"Detailed error info: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Error logging error: {e}")
    
    def log_debug(self, message: str, data: Dict[str, Any] = None, task_id: str = None):
        """记录调试信息
        
        Args:
            message: 消息
            data: 相关数据
            task_id: 任务ID（可选）
        """
        try:
            caller_info = self.get_caller_info()
            logger_name = f'task.{task_id}' if task_id else caller_info['module']
            logger = self.get_logger(logger_name)
            
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                'data': data or {},
                'caller': caller_info
            }
            
            # 格式化输出
            if data:
                logger.debug(f"Debug: {message} | Data: {json.dumps(data, ensure_ascii=False)}")
            else:
                logger.debug(f"Debug: {message}")
                
        except Exception as e:
            self.logger.error(f"Error logging debug info: {e}")
    
    def log_info(self, message: str, data: Dict[str, Any] = None, task_id: str = None):
        """记录信息
        
        Args:
            message: 消息
            data: 相关数据
            task_id: 任务ID（可选）
        """
        try:
            caller_info = self.get_caller_info()
            logger_name = f'task.{task_id}' if task_id else caller_info['module']
            logger = self.get_logger(logger_name)
            
            # 格式化输出
            if data:
                logger.info(f"Info: {message} | Data: {json.dumps(data, ensure_ascii=False)}")
            else:
                logger.info(f"Info: {message}")
                
        except Exception as e:
            self.logger.error(f"Error logging info: {e}")
    
    def log_warning(self, message: str, data: Dict[str, Any] = None, task_id: str = None):
        """记录警告
        
        Args:
            message: 消息
            data: 相关数据
            task_id: 任务ID（可选）
        """
        try:
            caller_info = self.get_caller_info()
            logger_name = f'task.{task_id}' if task_id else caller_info['module']
            logger = self.get_logger(logger_name)
            
            # 格式化输出
            if data:
                logger.warning(f"Warning: {message} | Data: {json.dumps(data, ensure_ascii=False)}")
            else:
                logger.warning(f"Warning: {message}")
                
        except Exception as e:
            self.logger.error(f"Error logging warning: {e}")
            
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
                        self.logger.info(f"Cleaned up old log file: {filename}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")
            raise 

# 全局日志管理器实例
_log_manager = None

def get_log_manager() -> LogManager:
    """获取全局日志管理器实例"""
    global _log_manager
    if _log_manager is None:
        # 使用默认配置
        config = {
            'log_dir': 'logs',
            'log_level': 'INFO'
        }
        _log_manager = LogManager(config)
    return _log_manager

def log_function_call(func):
    """函数调用日志装饰器"""
    def wrapper(*args, **kwargs):
        log_manager = get_log_manager()
        caller_info = log_manager.get_caller_info()
        
        try:
            # 记录函数调用开始
            log_manager.log_debug(
                f"Function call started: {func.__name__}",
                {
                    'args': str(args),
                    'kwargs': str(kwargs),
                    'caller': caller_info
                }
            )
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录函数调用成功
            log_manager.log_debug(
                f"Function call completed: {func.__name__}",
                {
                    'result_type': type(result).__name__,
                    'caller': caller_info
                }
            )
            
            return result
            
        except Exception as e:
            # 记录函数调用失败
            log_manager.log_error(
                None,  # 没有特定的task_id
                e,
                {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs),
                    'caller': caller_info
                }
            )
            raise
    
    return wrapper

def log_class_methods(cls):
    """类方法日志装饰器"""
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('_'):
            setattr(cls, attr_name, log_function_call(attr))
    return cls

# 便捷的日志函数
def log_debug(message: str, data: Dict[str, Any] = None, task_id: str = None):
    """记录调试信息"""
    get_log_manager().log_debug(message, data, task_id)

def log_info(message: str, data: Dict[str, Any] = None, task_id: str = None):
    """记录信息"""
    get_log_manager().log_info(message, data, task_id)

def log_warning(message: str, data: Dict[str, Any] = None, task_id: str = None):
    """记录警告"""
    get_log_manager().log_warning(message, data, task_id)

def log_error(message: str, error: Exception = None, data: Dict[str, Any] = None, task_id: str = None):
    """记录错误"""
    if error:
        get_log_manager().log_error(task_id, error, data)
    else:
        get_log_manager().log_error(task_id, Exception(message), data)