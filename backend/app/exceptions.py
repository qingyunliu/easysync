class AlertOperationError(Exception):
    """告警操作异常"""
    pass

class MonitorOperationError(Exception):
    """监控操作异常"""
    pass

class EventOperationError(Exception):
    """事件操作异常"""
    pass

class StorageOperationError(Exception):
    """存储操作异常"""
    pass

class ClientOperationError(Exception):
    """客户端操作异常"""
    pass

class NodeOperationError(Exception):
    """节点操作异常"""
    pass

class TaskOperationError(Exception):
    """任务操作异常"""
    pass

class UserOperationError(Exception):
    """用户操作异常"""
    pass

class NotificationOperationError(Exception):
    """通知操作异常"""
    pass 