import os
import json
import logging
import logging.handlers
import traceback
import inspect
from typing import Dict, Any, Optional
from datetime import datetime

class LogManager:
    """统一的日志管理类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.setup_logging()
        
    def setup_logging(self, force: bool = False):
        """设置全局日志配置
        
        Args:
            force: 是否强制重新配置
        """
        root_logger = logging.getLogger()
        
        # 如果强制重新配置，先清除现有处理器
        if force and root_logger.handlers:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
        
        # 如果已经有处理器且不强制重新配置，直接返回
        if root_logger.handlers and not force:
            return
        
        # 创建日志目录
        log_dir = self.config.get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志级别
        log_level = self.config.get('log_level', 'INFO')
        if isinstance(log_level, str):
            log_level = getattr(logging, log_level.upper(), logging.INFO)
        root_logger.setLevel(log_level)
        
        # 创建统一的格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d %(process)d %(name)s %(levelname)s [%(pathname)s:%(lineno)d] - %(funcName)s() [-] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level) 
        console_handler.setFormatter(formatter)
        
        # 根据日志级别选择文件名
        log_filename = 'app.debug.log' if log_level == logging.DEBUG else 'app.log'
        
        # 创建文件处理器（使用轮转文件处理器）
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, log_filename),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level) 
        file_handler.setFormatter(formatter)
        
        # 添加处理器到根日志记录器
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # 确保所有子日志记录器都继承配置
        self._configure_child_loggers()
        
    def _configure_child_loggers(self):
        """配置子日志记录器"""
        # 获取所有已存在的日志记录器
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        loggers.append(logging.getLogger())  # 添加根日志记录器
        
        for logger in loggers:
            logger.propagate = True
            if not logger.handlers:
                logger.handlers = []
        
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        logger = logging.getLogger(name)
        
        # 确保日志记录器使用正确的配置
        if not logger.handlers:
            logger.propagate = True
        return logger
    
    def get_caller_info(self) -> Dict[str, str]:
        """获取调用者信息
        
        Returns:
            Dict[str, str]: 调用者信息
        """
        try:
            # 获取调用栈信息
            frame = inspect.currentframe()
            if frame:
                # 向上查找调用者
                caller_frame = frame.f_back
                if caller_frame:
                    filename = caller_frame.f_code.co_filename
                    lineno = caller_frame.f_lineno
                    funcname = caller_frame.f_code.co_name
                    
                    return {
                        'file': os.path.basename(filename),
                        'line': str(lineno),
                        'function': funcname
                    }
        except Exception:
            pass
        
        return {
            'file': 'unknown',
            'line': '0',
            'function': 'unknown'
        }
    
    def log_task_event(self, task_id: str, event_type: str, data: Dict[str, Any]):
        """记录任务事件
        
        Args:
            task_id: 任务ID
            event_type: 事件类型
            data: 事件数据
        """
        logger = self.get_logger('task')
        caller_info = self.get_caller_info()
        
        log_data = {
            'task_id': task_id,
            'event_type': event_type,
            'data': data,
            'caller': caller_info
        }
        
        logger.info(f"Task event: {event_type}", extra={'log_data': log_data})
    
    def log_error(self, task_id: str, error: Exception, context: Dict[str, Any] = None):
        """记录错误信息
        
        Args:
            task_id: 任务ID
            error: 错误对象
            context: 上下文信息
        """
        logger = self.get_logger('error')
        caller_info = self.get_caller_info()
        
        error_data = {
            'task_id': task_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'caller': caller_info
        }
        
        logger.error(f"Error in task {task_id}: {str(error)}", extra={'log_data': error_data})
    
    def log_debug(self, message: str, data: Dict[str, Any] = None, task_id: str = None):
        """记录调试信息
        
        Args:
            message: 消息
            data: 数据
            task_id: 任务ID
        """
        logger = self.get_logger('debug')
        caller_info = self.get_caller_info()
        
        log_data = {
            'message': message,
            'data': data or {},
            'task_id': task_id,
            'caller': caller_info
        }
        
        logger.debug(message, extra={'log_data': log_data})
    
    def log_info(self, message: str, data: Dict[str, Any] = None, task_id: str = None):
        """记录信息
        
        Args:
            message: 消息
            data: 数据
            task_id: 任务ID
        """
        logger = self.get_logger('info')
        caller_info = self.get_caller_info()
        
        log_data = {
            'message': message,
            'data': data or {},
            'task_id': task_id,
            'caller': caller_info
        }
        
        logger.info(message, extra={'log_data': log_data})
    
    def log_warning(self, message: str, data: Dict[str, Any] = None, task_id: str = None):
        """记录警告信息
        
        Args:
            message: 消息
            data: 数据
            task_id: 任务ID
        """
        logger = self.get_logger('warning')
        caller_info = self.get_caller_info()
        
        log_data = {
            'message': message,
            'data': data or {},
            'task_id': task_id,
            'caller': caller_info
        }
        
        logger.warning(message, extra={'log_data': log_data})
    
    def cleanup_old_logs(self, max_age_days: int = 30):
        """清理旧日志文件
        
        Args:
            max_age_days: 最大保留天数
        """
        try:
            log_dir = self.config.get('log_dir', 'logs')
            if not os.path.exists(log_dir):
                return
            
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = os.path.getmtime(file_path)
                        if file_time < cutoff_time:
                            os.remove(file_path)
                            self.log_info(f"Cleaned up old log file: {filename}")
                            
        except Exception as e:
            self.log_error(None, e, {'operation': 'cleanup_old_logs'})

# 全局日志管理器实例
_log_manager = None

def init_logging(config: Dict[str, Any] = None) -> LogManager:
    """初始化日志系统
    
    Args:
        config: 日志配置
        
    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager
    
    if _log_manager is None:
        _log_manager = LogManager(config)
    
    return _log_manager

def get_log_manager() -> LogManager:
    """获取日志管理器实例
    
    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager
    
    if _log_manager is None:
        _log_manager = LogManager()
    
    return _log_manager

def force_setup_logging(config: Dict[str, Any] = None) -> LogManager:
    """强制重新设置日志配置
    
    Args:
        config: 日志配置
        
    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager
    
    _log_manager = LogManager(config)
    _log_manager.setup_logging(force=True)
    
    return _log_manager

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    log_manager = get_log_manager()
    return log_manager.get_logger(name)

def log_debug(message: str, data: Dict[str, Any] = None, task_id: str = None):
    """记录调试信息"""
    log_manager = get_log_manager()
    log_manager.log_debug(message, data, task_id)

def log_info(message: str, data: Dict[str, Any] = None, task_id: str = None):
    """记录信息"""
    log_manager = get_log_manager()
    log_manager.log_info(message, data, task_id)

def log_warning(message: str, data: Dict[str, Any] = None, task_id: str = None):
    """记录警告信息"""
    log_manager = get_log_manager()
    log_manager.log_warning(message, data, task_id)

def log_error(message: str, error: Exception = None, data: Dict[str, Any] = None, task_id: str = None):
    """记录错误信息"""
    log_manager = get_log_manager()
    if error:
        log_manager.log_error(task_id, error, data)
    else:
        log_manager.log_warning(message, data, task_id)

def log_function_call(func):
    """函数调用日志装饰器"""
    def wrapper(*args, **kwargs):
        logger = get_logger('function_call')
        func_name = func.__name__
        logger.debug(f"Calling function: {func_name}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func_name} failed: {str(e)}")
            raise
    return wrapper

def _auto_init():
    """自动初始化日志系统"""
    try:
        # 尝试从环境变量或配置文件读取配置
        config = {
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_dir': os.getenv('LOG_DIR', 'logs')
        }
        init_logging(config)
    except Exception:
        # 如果初始化失败，使用默认配置
        init_logging()

# 自动初始化
_auto_init()