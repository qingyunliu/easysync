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
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
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
        log_filename = 'agent.debug.log' if log_level == logging.DEBUG else 'agent.log'
        
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
            stack = inspect.stack()
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
        """记录错误"""
        try:
            logger = self.get_logger(f'task.{task_id}' if task_id else 'error')
            stack_trace = traceback.format_exc()
            
            logger.error(
                f"Error: {type(error).__name__} | Task: {task_id or 'N/A'} | "
                f"Message: {str(error)} | Context: {json.dumps(context or {}, ensure_ascii=False)}"
            )
            
            # 详细错误信息记录到DEBUG级别
            logger.debug(f"Stack trace: {stack_trace}")
            
        except Exception as e:
            self.get_logger('LogManager').error(f"Error logging error: {e}")
    
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
            self.get_logger('LogManager').error(f"Error logging debug info: {e}")
    
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
            
            if data:
                logger.info(f"Info: {message} | Data: {json.dumps(data, ensure_ascii=False)}")
            else:
                logger.info(f"Info: {message}")
                
        except Exception as e:
            self.get_logger('LogManager').error(f"Error logging info: {e}")
    
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
                        self.get_logger('LogManager').info(f"Cleaned up old log file: {filename}")
                        
        except Exception as e:
            self.get_logger('LogManager').error(f"Error cleaning up old logs: {e}")
            raise 

# 全局日志管理器实例
_log_manager = None

def init_logging(config: Dict[str, Any] = None) -> LogManager:
    """初始化日志系统
    
    Args:
        config: 日志配置，如果为None则使用默认配置
        
    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager
    
    if config is None:
        config = {
            'log_dir': 'logs',
            'log_level': 'INFO'
        }
    
    # 如果已经初始化，检查配置是否相同
    if _log_manager is not None:
        current_config = _log_manager.config
        if (current_config.get('log_dir') == config.get('log_dir') and 
            current_config.get('log_level') == config.get('log_level')):
            return _log_manager
        else:
            # 配置不同，强制重新配置
            _log_manager = LogManager(config)
            _log_manager.setup_logging(force=True)
            return _log_manager
    
    # 创建新的日志管理器
    _log_manager = LogManager(config)
    return _log_manager

def get_log_manager() -> LogManager:
    """获取全局日志管理器实例"""
    global _log_manager
    if _log_manager is None:
        _log_manager = init_logging()
    return _log_manager

def force_setup_logging(config: Dict[str, Any] = None) -> LogManager:
    """强制重新设置日志配置"""
    global _log_manager
    
    if config is None:
        config = {
            'log_dir': 'logs',
            'log_level': 'INFO'
        }
    
    _log_manager = LogManager(config)
    _log_manager.setup_logging(force=True)
    return _log_manager

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

# 装饰器
def log_function_call(func):
    """函数调用日志装饰器"""
    def wrapper(*args, **kwargs):
        log_manager = get_log_manager()
        
        try:
            log_manager.log_debug(f"Function call started: {func.__name__}")
            result = func(*args, **kwargs)
            log_manager.log_debug(f"Function call completed: {func.__name__}")
            return result
        except Exception as e:
            log_manager.log_error(None, e, {'function': func.__name__})
            raise
    
    return wrapper

# 模块导入时自动初始化
def _auto_init():
    """自动初始化日志系统"""
    try:
        if _log_manager is None:
            init_logging()
    except Exception as e:
        # 使用标准logging作为后备，因为日志管理器初始化失败
        import logging
        logging.warning(f"Failed to auto-initialize logging: {e}")

_auto_init()