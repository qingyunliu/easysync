import time
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps

class RetryHandler:
    """重试处理类"""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        self.logger = logging.getLogger('RetryHandler')
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        
    def retry(self, func: Callable) -> Callable:
        """重试装饰器
        
        Args:
            func: 要重试的函数
            
        Returns:
            Callable: 包装后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = self.delay
            
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= self.backoff
                    else:
                        self.logger.error(
                            f"All {self.max_retries} attempts failed. "
                            f"Last error: {str(e)}"
                        )
                        
            raise last_exception
            
        return wrapper
        
    def retry_with_config(self, config: Dict[str, Any]) -> Callable:
        """使用配置的重试装饰器
        
        Args:
            config: 重试配置
                {
                    'max_retries': 3,
                    'delay': 1.0,
                    'backoff': 2.0
                }
                
        Returns:
            Callable: 重试装饰器
        """
        max_retries = config.get('max_retries', self.max_retries)
        delay = config.get('delay', self.delay)
        backoff = config.get('backoff', self.backoff)
        
        return RetryHandler(max_retries, delay, backoff).retry
        
class RetryableOperation:
    """可重试操作类"""
    
    def __init__(self, retry_handler: RetryHandler):
        self.retry_handler = retry_handler
        
    @property
    def retry(self):
        """获取重试装饰器"""
        return self.retry_handler.retry
        
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """执行可重试操作
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        return self.retry(func)(*args, **kwargs)
        
    def execute_with_config(self, func: Callable, config: Dict[str, Any], *args, **kwargs) -> Any:
        """使用配置执行可重试操作
        
        Args:
            func: 要执行的函数
            config: 重试配置
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        return self.retry_handler.retry_with_config(config)(func)(*args, **kwargs) 