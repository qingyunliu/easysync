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
    try:
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, dict):
            return {k: clean_serializable_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [clean_serializable_data(item) for item in data]
        elif isinstance(data, tuple):
            return [clean_serializable_data(item) for item in data]
        elif isinstance(data, Response):
            # 处理Flask Response对象
            try:
                return {
                    'type': 'Response',
                    'status_code': getattr(data, 'status_code', None),
                    'status': getattr(data, 'status', None),
                    'headers': dict(data.headers) if hasattr(data, 'headers') else {},
                    'content_length': getattr(data, 'content_length', None)
                }
            except Exception:
                return f"<Response object: {type(data).__name__}>"
        elif hasattr(data, '__dict__'):
            # 处理其他对象，尝试转换为字典
            try:
                # 先尝试获取基本属性
                if hasattr(data, 'to_dict'):
                    return clean_serializable_data(data.to_dict())
                elif hasattr(data, 'to_json'):
                    return clean_serializable_data(data.to_json())
                else:
                    # 尝试获取对象的字典表示
                    obj_dict = {}
                    for key, value in data.__dict__.items():
                        if not key.startswith('_'):  # 跳过私有属性
                            obj_dict[key] = clean_serializable_data(value)
                    return obj_dict
            except Exception:
                return f"<{type(data).__name__} object>"
        else:
            # 对于其他类型，尝试转换为字符串
            try:
                return str(data)
            except Exception:
                return f"<{type(data).__name__} object>"
    except Exception as e:
        return f"<Error serializing {type(data).__name__}: {str(e)}>"


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
                'request_method': request.method,
                'request_path': request.path,
                'request_args': dict(request.args),
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.remote_addr
            }
            
            # 只有当result不是Response对象时才包含它
            if not isinstance(result, Response):
                event_details['result'] = clean_serializable_data(result)
            else:
                # 对于Response对象，只包含基本信息
                event_details['result'] = {
                    'type': 'Response',
                    'status_code': getattr(result, 'status_code', None)
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
                # 映射事件动作到告警策略中使用的代码
                action_mapping = {
                    'create': 'add_storage',
                    'delete': 'delete_storage',
                    'update': 'update_storage',
                    'test': 'test_storage_connection',
                    'info': 'get_storage_info'
                }
                mapped_action = action_mapping.get(event_action, event_action)
                
                # 记录成功事件
                event_middleware._record_event_success(
                    'storage', mapped_action, result,
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
                # 映射事件动作到告警策略中使用的代码
                action_mapping = {
                    'create': 'node_add',
                    'delete': 'node_delete',
                    'update': 'node_update',
                    'connect': 'node_connect',
                    'disconnect': 'node_disconnect',
                    'heartbeat': 'node_heartbeat',
                    'install': 'node_agent_install',
                    'uninstall': 'node_agent_uninstall',
                    'upgrade': 'node_agent_upgrade',
                    'group_change': 'node_group_change'
                }
                mapped_action = action_mapping.get(event_action, event_action)
                
                # 记录成功事件
                event_middleware._record_event_success(
                    'node', mapped_action, result,  # 使用 'node' 类型而不是 'agent'
                    f"节点操作 {event_action} 成功",
                    {'node_id': node_id} if node_id else None
                )
                return result
            except Exception as e:
                # 记录失败事件
                event_middleware._record_event_failure(
                    'node', event_action, e,  # 使用 'node' 类型而不是 'agent'
                    f"节点操作 {event_action} 失败",
                    {'node_id': node_id} if node_id else None
                )
                raise
        return wrapper
    return decorator 