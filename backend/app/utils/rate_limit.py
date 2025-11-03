"""
API限流工具
使用Redis实现分布式限流
"""
import time
import logging
from functools import wraps
from flask import request, jsonify
from typing import Callable, Optional, Tuple, Dict
from .cache import get_redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """限流器"""
    
    def __init__(self, key_func: Optional[Callable] = None):
        """
        初始化限流器
        
        Args:
            key_func: 自定义键生成函数，接收request对象，返回限流键
        """
        self.key_func = key_func or self._default_key_func
    
    def _default_key_func(self, request_obj) -> str:
        """默认键生成：使用IP地址"""
        ip = request_obj.headers.get('X-Forwarded-For', request_obj.remote_addr)
        return f"rate_limit:ip:{ip}"
    
    def is_allowed(self, limit: int, window: int, key: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        检查是否允许请求
        
        Args:
            limit: 时间窗口内允许的请求数
            window: 时间窗口（秒）
            key: 限流键，如果不提供则使用key_func生成
        
        Returns:
            (is_allowed, info): is_allowed表示是否允许，info包含限流信息
        """
        if not key:
            key = self.key_func(request)
        
        redis_client = get_redis_client()
        if not redis_client:
            # Redis不可用时，允许请求通过（降级处理）
            logger.warning("Rate limiter: Redis not available, allowing request")
            return True, {'limit': limit, 'remaining': limit, 'reset': int(time.time()) + window}
        
        try:
            now = time.time()
            window_start = now - (now % window)
            redis_key = f"{key}:{int(window_start)}"
            
            # 使用INCR操作原子性增加计数
            current = redis_client.incr(redis_key)
            
            # 如果是新键，设置过期时间
            if current == 1:
                redis_client.expire(redis_key, window)
            
            # 检查是否超过限制
            is_allowed = current <= limit
            remaining = max(0, limit - current)
            reset_time = int(window_start) + window
            
            return is_allowed, {
                'limit': limit,
                'remaining': remaining,
                'reset': reset_time
            }
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # 出错时允许请求通过（容错）
            return True, {'limit': limit, 'remaining': limit, 'reset': int(time.time()) + window}


def rate_limit(limit: int = 100, window: int = 60, key_func: Optional[Callable] = None):
    """
    API限流装饰器
    
    Args:
        limit: 时间窗口内允许的请求数（默认100）
        window: 时间窗口（秒，默认60）
        key_func: 自定义键生成函数
    
    Example:
        @rate_limit(limit=10, window=60)  # 每分钟10次
        @rate_limit(limit=100, window=3600, key_func=lambda r: f"user:{get_jwt_identity()}")  # 每小时100次/用户
    """
    limiter = RateLimiter(key_func=key_func)
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_allowed, info = limiter.is_allowed(limit, window)
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for {info.get('key', 'unknown')}")
                response = jsonify({
                    'status': 'error',
                    'message': '请求过于频繁，请稍后再试',
                    'error_code': 'RATE_LIMIT_EXCEEDED',
                    'limit': info['limit'],
                    'reset': info['reset']
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
                return response
            
            # 添加限流信息到响应头
            response = func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
            return response
        
        return wrapper
    return decorator


def user_rate_limit(limit: int = 100, window: int = 60):
    """
    基于用户的限流装饰器
    
    Args:
        limit: 时间窗口内允许的请求数
        window: 时间窗口（秒）
    """
    def key_func(request_obj):
        from flask_jwt_extended import get_jwt_identity
        try:
            user_id = get_jwt_identity()
            return f"rate_limit:user:{user_id}"
        except Exception:
            # 如果无法获取用户ID，回退到IP限流
            ip = request_obj.headers.get('X-Forwarded-For', request_obj.remote_addr)
            return f"rate_limit:ip:{ip}"
    
    return rate_limit(limit=limit, window=window, key_func=key_func)

