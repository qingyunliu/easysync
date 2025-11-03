"""
缓存工具类
使用Redis进行数据缓存，提升性能
"""
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps
from flask import current_app
import redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

# 全局Redis连接池
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """获取Redis客户端实例（懒加载）"""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        # 测试连接
        _redis_client.ping()
        logger.info("Redis cache connection established")
        return _redis_client
    except (RedisError, RedisConnectionError, AttributeError) as e:
        logger.warning(f"Redis cache not available: {e}. Falling back to no-cache mode.")
        return None


def is_cache_available() -> bool:
    """检查缓存是否可用"""
    try:
        client = get_redis_client()
        if client:
            client.ping()
            return True
    except Exception:
        pass
    return False


class CacheManager:
    """缓存管理器"""
    
    DEFAULT_TTL = 3600  # 默认1小时过期
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            client = get_redis_client()
            if not client:
                return default
            
            value = client.get(key)
            if value is None:
                return default
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return default
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """设置缓存值"""
        try:
            client = get_redis_client()
            if not client:
                return False
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """删除缓存"""
        try:
            client = get_redis_client()
            if not client:
                return False
            
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """按模式删除缓存"""
        try:
            client = get_redis_client()
            if not client:
                return 0
            
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete_pattern error for pattern {pattern}: {e}")
            return 0
    
    @staticmethod
    def clear_user_cache(user_id: str):
        """清除用户相关缓存"""
        patterns = [
            f"user:{user_id}:*",
            f"user_profile:{user_id}",
            f"user_stats:{user_id}:*",
        ]
        count = 0
        for pattern in patterns:
            count += CacheManager.delete_pattern(pattern)
        logger.debug(f"Cleared {count} cache entries for user {user_id}")
        return count


def cached(ttl: int = CacheManager.DEFAULT_TTL, key_prefix: str = "", key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 键前缀
        key_func: 自定义键生成函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # 尝试从缓存获取
            cached_value = CacheManager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # 缓存未命中，执行函数
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # 存储到缓存
            CacheManager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """使缓存失效的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 执行函数后清除相关缓存
            CacheManager.delete_pattern(pattern)
            return result
        return wrapper
    return decorator

