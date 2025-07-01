class TaskError(Exception):
    """任务错误基类"""
    pass

class TaskNotFoundError(TaskError):
    """任务不存在错误"""
    pass

class TaskOperationError(TaskError):
    """任务操作错误"""
    pass

class TaskValidationError(TaskError):
    """任务验证错误"""
    pass

class TaskStateError(TaskError):
    """任务状态错误"""
    pass

class TaskResourceError(TaskError):
    """任务资源错误"""
    pass 