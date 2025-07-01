class MonitorError(Exception):
    """监控错误基类"""
    pass

class MonitorNotFoundError(MonitorError):
    """监控数据不存在错误"""
    pass

class MonitorValidationError(MonitorError):
    """监控数据验证错误"""
    pass

class MonitorOperationError(MonitorError):
    """监控操作错误"""
    pass

class AlertRuleError(MonitorError):
    """告警规则错误"""
    pass

class AlertNotificationError(MonitorError):
    """告警通知错误"""
    pass 