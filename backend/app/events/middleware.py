import logging
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, g, current_app, Response
from flask_jwt_extended import get_jwt_identity
from backend.app.models.event import Event
from backend.app.events.service import EventService

logger = logging.getLogger(__name__)


def clean_serializable_data(data: Any) -> Any:
    """清理数据，确保可以序列化为JSON"""
    if isinstance(data, dict):
        return {k: clean_serializable_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_serializable_data(item) for item in data]
    elif isinstance(data, Response):
        # 处理Flask Response对象
        return {
            'type': 'Response',
            'status_code': data.status_code,
            'status': data.status,
            'headers': dict(data.headers),
            'content_length': data.content_length
        }
    elif hasattr(data, '__dict__'):
        # 处理其他对象，尝试转换为字典
        try:
            return str(data)
        except:
            return f"<{type(data).__name__} object>"
    else:
        return data


class EventMiddleware:
    """事件记录中间件"""
    
    def __init__(self):
        self.event_service = EventService()
    
    def record_event(self, event_type: str, event_action: str, 
                    event_result: str = None, message: str = None, 
                    details: Dict[str, Any] = None):
        """记录事件的装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 执行原始函数
                try:
                    result = func(*args, **kwargs)
                    # 成功时记录事件
                    self._record_event_success(event_type, event_action, result, message, details)
                    return result
                except Exception as e:
                    # 失败时记录事件
                    self._record_event_failure(event_type, event_action, e, message, details)
                    raise
            return wrapper
        return decorator
    
    def _record_event_success(self, event_type: str, event_action: str, 
                            result: Any, message: str = None, details: Dict[str, Any] = None):
        """记录成功事件"""
        try:
            # 获取用户信息
            user_id = get_jwt_identity()
            if not user_id:
                return
            
            # 构建事件详情
            event_details = {
                'result': clean_serializable_data(result),
                'request_method': request.method,
                'request_path': request.path,
                'request_args': dict(request.args),
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.remote_addr
            }
            if details:
                event_details.update(clean_serializable_data(details))
            
            # 记录成功事件 - 使用EventService来触发告警评估
            self.event_service.create_event(
                user_id=user_id,
                event_type=event_type,
                event_action=event_action,
                event_result='success',
                message=message or f"{event_type} {event_action} 成功",
                details=event_details
            )
            
        except Exception as e:
            logger.error(f"Error recording success event: {e}")
    
    def _record_event_failure(self, event_type: str, event_action: str, 
                            error: Exception, message: str = None, details: Dict[str, Any] = None):
        """记录失败事件"""
        try:
            # 获取用户信息
            user_id = get_jwt_identity()
            if not user_id:
                return
            
            # 构建事件详情
            event_details = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'request_method': request.method,
                'request_path': request.path,
                'request_args': dict(request.args),
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.remote_addr
            }
            if details:
                event_details.update(clean_serializable_data(details))
            
            # 记录失败事件 - 使用EventService来触发告警评估
            self.event_service.create_event(
                user_id=user_id,
                event_type=event_type,
                event_action=event_action,
                event_result='failed',
                message=message or f"{event_type} {event_action} 失败: {str(error)}",
                details=event_details
            )
            
        except Exception as e:
            logger.error(f"Error recording failure event: {e}")


# 全局事件中间件实例
event_middleware = EventMiddleware()


def record_api_event(event_type: str, event_action: str, 
                    success_message: str = None, failure_message: str = None,
                    details: Dict[str, Any] = None):
    """API事件记录装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # 记录成功事件
                event_middleware._record_event_success(
                    event_type, event_action, result, 
                    success_message, details
                )
                return result
            except Exception as e:
                # 记录失败事件
                event_middleware._record_event_failure(
                    event_type, event_action, e, 
                    failure_message, details
                )
                raise
        return wrapper
    return decorator


def record_storage_event(event_action: str, storage_id: str = None):
    """存储事件记录装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # 记录成功事件
                event_middleware._record_event_success(
                    'storage', event_action, result,
                    f"存储操作 {event_action} 成功",
                    {'storage_id': storage_id} if storage_id else None
                )
                return result
            except Exception as e:
                # 记录失败事件
                event_middleware._record_event_failure(
                    'storage', event_action, e,
                    f"存储操作 {event_action} 失败",
                    {'storage_id': storage_id} if storage_id else None
                )
                raise
        return wrapper
    return decorator


def record_client_event(event_action: str, client_id: str = None):
    """客户端事件记录装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # 记录成功事件
                event_middleware._record_event_success(
                    'client', event_action, result,
                    f"客户端操作 {event_action} 成功",
                    {'client_id': client_id} if client_id else None
                )
                return result
            except Exception as e:
                # 记录失败事件
                event_middleware._record_event_failure(
                    'client', event_action, e,
                    f"客户端操作 {event_action} 失败",
                    {'client_id': client_id} if client_id else None
                )
                raise
        return wrapper
    return decorator


def record_agent_event(event_action: str, node_id: str = None):
    """代理事件记录装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # 记录成功事件
                event_middleware._record_event_success(
                    'agent', event_action, result,
                    f"代理操作 {event_action} 成功",
                    {'node_id': node_id} if node_id else None
                )
                return result
            except Exception as e:
                # 记录失败事件
                event_middleware._record_event_failure(
                    'agent', event_action, e,
                    f"代理操作 {event_action} 失败",
                    {'node_id': node_id} if node_id else None
                )
                raise
        return wrapper
    return decorator 