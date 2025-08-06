# 统一日志管理器使用指南

## 概述

`logger.py` 提供了一个统一的日志管理解决方案，确保整个应用程序使用一致的日志格式和配置。

## 主要特性

- **统一配置**: 所有模块使用相同的日志格式和配置
- **自动初始化**: 模块导入时自动初始化日志系统
- **多种使用方式**: 提供便捷函数、管理器实例、装饰器等多种使用方式
- **任务相关日志**: 专门支持任务事件的日志记录
- **错误追踪**: 自动记录错误堆栈和上下文信息

## 初始化

### 在应用启动时初始化

```python
from utils.logger import init_logging

# 使用默认配置
log_manager = init_logging()

# 或使用自定义配置
config = {
    'log_dir': 'logs',
    'log_level': 'DEBUG'
}
log_manager = init_logging(config)
```

### 在 proxy.py 中的使用

```python
# 设置日志配置
log_config = {
    'log_dir': os.path.join(os.path.dirname(__file__), 'logs'),
    'log_level': args.log_level
}

# 初始化日志系统
log_manager = init_logging(log_config)
```

## 使用方式

### 1. 便捷函数（推荐）

```python
from utils.logger import log_info, log_debug, log_warning, log_error

def my_function():
    log_info("开始执行函数")

    try:
        result = do_something()
        log_debug("操作完成", {"result": result})
        return result
    except Exception as e:
        log_error("执行失败", e, {"context": "my_function"})
        raise
```

### 2. 日志管理器实例

```python
from utils.logger import get_log_manager

def my_function():
    log_manager = get_log_manager()

    # 获取特定名称的日志记录器
    logger = log_manager.get_logger("my.module")
    logger.info("使用管理器实例记录日志")

    # 记录任务事件
    log_manager.log_task_event(
        task_id="task_001",
        event_type="task_started",
        data={"source": "test", "target": "test"}
    )
```

### 3. 装饰器

```python
from utils.logger import log_function_call

@log_function_call
def decorated_function(param1, param2):
    return f"处理参数: {param1}, {param2}"
```

### 4. 在类中使用

```python
from utils.logger import get_log_manager

class MyClass:
    def __init__(self):
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger("MyClass")

    def do_something(self):
        self.logger.info("开始执行操作")
        # ... 执行操作
        self.logger.debug("操作完成")
```

### 5. 直接使用 logging 模块

```python
import logging

# 会自动使用我们配置的格式
logger = logging.getLogger(__name__)
logger.info("这是模块级别的日志")
logger.debug("调试信息")
```

## 日志级别

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息

## 日志格式

统一的日志格式包含：

- 时间戳
- 日志记录器名称
- 日志级别
- 文件名和行号
- 函数名
- 消息内容

示例：

```
2024-01-15 10:30:45 - my.module - INFO - [my_file.py:25] - my_function() - 开始执行操作
```

## 文件输出

- **控制台输出**: INFO 级别及以上
- **文件输出**: DEBUG 级别及以上
- **文件轮转**: 10MB 大小限制，保留 5 个备份文件
- **编码**: UTF-8

## 任务相关日志

专门为任务执行提供的事件日志：

```python
log_manager.log_task_event(
    task_id="task_001",
    event_type="task_started",
    data={"source": "nas", "target": "obs"}
)

log_manager.log_error(
    task_id="task_001",
    error=exception,
    context={"step": "sync", "progress": "50%"}
)
```

## 最佳实践

1. **在应用启动时初始化**: 确保在应用启动时调用 `init_logging()`
2. **使用便捷函数**: 对于简单的日志记录，使用 `log_info()`, `log_debug()` 等便捷函数
3. **合理使用日志级别**:
   - DEBUG: 详细的调试信息
   - INFO: 重要的业务信息
   - WARNING: 需要注意但不影响运行的情况
   - ERROR: 错误和异常
4. **包含上下文信息**: 在记录错误时包含相关的上下文数据
5. **避免重复配置**: 不要在多个地方重复配置日志系统

## 注意事项

- 日志管理器是单例模式，全局只有一个实例
- 模块导入时会自动初始化（使用默认配置）
- 如果需要自定义配置，请在应用启动时调用 `init_logging(config)`
- 所有子日志记录器都会继承根日志记录器的配置
