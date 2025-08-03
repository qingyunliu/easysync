# 事件告警系统

## 概述

事件告警系统是基于服务端接口调用事件进行告警的机制。当用户调用各种API接口时，系统会自动记录事件到事件数据库，然后根据配置的告警策略进行告警评估和通知。

## 系统架构

### 1. 事件记录层
- **事件中间件** (`backend/app/events/middleware.py`): 提供事件记录装饰器
- **事件服务** (`backend/app/events/service.py`): 处理事件创建和告警评估
- **事件模型** (`backend/app/models/event.py`): 事件数据模型

### 2. 告警评估层
- **告警评估器** (`backend/app/alerts/evaluator.py`): 评估事件是否触发告警策略
- **告警策略** (`backend/app/models/alert.py`): 告警策略配置模型

### 3. 通知层
- **告警服务** (`backend/app/alerts/services.py`): 发送告警通知
- **通知服务** (`backend/app/notifications/services.py`): 处理通知发送

## 事件类型

系统支持以下事件类型：

### 1. 存储事件 (storage)
- `create`: 创建存储节点
- `update`: 更新存储节点
- `delete`: 删除存储节点
- `test_connection`: 测试连接
- `list_buckets`: 获取存储桶列表
- `list_objects`: 获取对象列表
- `list_files`: 获取文件列表
- `download`: 下载文件
- `mount_check`: 检查挂载状态

### 2. 客户端事件 (client)
- `create`: 创建客户端
- `update`: 更新客户端
- `delete`: 删除客户端
- `connect`: 连接客户端
- `disconnect`: 断开客户端

### 3. 代理事件 (agent)
- `create`: 创建代理节点
- `update`: 更新代理节点
- `delete`: 删除代理节点
- `start`: 启动代理
- `stop`: 停止代理
- `restart`: 重启代理

### 4. 系统事件 (system)
- `login`: 用户登录
- `logout`: 用户登出
- `password_change`: 密码修改
- `profile_update`: 个人信息更新

## 事件结果

事件结果包括：
- `success`: 操作成功
- `failed`: 操作失败
- `timeout`: 操作超时
- `error`: 发生错误
- `warning`: 警告信息

## 使用方法

### 1. 在路由中使用事件记录装饰器

```python
from backend.app.events.middleware import record_storage_event, record_client_event, record_agent_event

# 存储事件记录
@storages_bp.route('', methods=['POST'])
@require_user
@record_storage_event('create')
def create_storage():
    # 路由逻辑
    pass

# 带参数的事件记录（用于获取资源ID）
@storages_bp.route('/<string:storage_id>', methods=['DELETE'])
@require_user
@record_storage_event('delete', lambda storage_id: storage_id)
def delete_storage(storage_id):
    # 路由逻辑
    pass
```

### 2. 配置事件告警策略

通过API或管理界面创建事件告警策略：

```json
{
  "name": "存储操作失败告警",
  "description": "当存储操作失败时发送告警",
  "level": "warning",
  "enabled": true,
  "policy_type": "event",
  "event_type": "storage",
  "event_actions": ["create", "update", "delete", "test_connection"],
  "event_results": ["failed", "error", "timeout"],
  "monitored_resources": ["storage_1", "storage_2"],
  "notification_targets": ["email_1", "webhook_1"],
  "trigger_rules": {
    "frequency_limit": {
      "time_window": 3600,
      "max_count": 5
    }
  }
}
```

### 3. 事件告警策略配置说明

#### 基本配置
- `name`: 策略名称
- `description`: 策略描述
- `level`: 告警级别 (info, warning, error, critical)
- `enabled`: 是否启用
- `policy_type`: 策略类型，事件告警固定为 "event"

#### 事件匹配配置
- `event_type`: 事件类型 (storage, client, agent, system)
- `event_actions`: 事件动作列表
- `event_results`: 事件结果列表
- `monitored_resources`: 监控的资源ID列表（可选）

#### 频率限制配置
```json
{
  "trigger_rules": {
    "frequency_limit": {
      "time_window": 3600,  // 时间窗口（秒）
      "max_count": 5         // 最大事件数量
    }
  }
}
```

## API接口

### 1. 事件管理接口

#### 获取事件列表
```
GET /api/events/
参数:
- event_type: 事件类型
- event_action: 事件动作
- event_result: 事件结果
- start_time: 开始时间
- end_time: 结束时间
- page: 页码
- per_page: 每页数量
```

#### 获取事件统计
```
GET /api/events/statistics
参数:
- days: 统计天数（默认7天）
```

#### 获取事件告警统计
```
GET /api/events/alert-statistics
参数:
- days: 统计天数（默认7天）
```

#### 获取事件详情
```
GET /api/events/<event_id>
```

#### 获取事件类型列表
```
GET /api/events/types
```

#### 获取事件动作列表
```
GET /api/events/actions
参数:
- event_type: 事件类型（可选）
```

#### 获取事件结果列表
```
GET /api/events/results
```

#### 清理旧事件
```
POST /api/events/cleanup
参数:
- days: 保留天数（默认30天）
```

#### 导出事件数据
```
GET /api/events/export
参数:
- event_type: 事件类型
- event_action: 事件动作
- event_result: 事件结果
- start_time: 开始时间
- end_time: 结束时间
```

### 2. 告警策略管理接口

#### 创建事件告警策略
```
POST /api/alerts/policies
{
  "name": "存储操作失败告警",
  "description": "当存储操作失败时发送告警",
  "level": "warning",
  "enabled": true,
  "policy_type": "event",
  "event_type": "storage",
  "event_actions": ["create", "update", "delete"],
  "event_results": ["failed", "error"],
  "notification_targets": ["email_1"],
  "trigger_rules": {
    "frequency_limit": {
      "time_window": 3600,
      "max_count": 5
    }
  }
}
```

## 告警实例

当事件触发告警策略时，系统会创建告警实例：

```json
{
  "id": "alert_instance_id",
  "policy_id": "policy_id",
  "alert_name": "存储操作失败告警",
  "severity": "warning",
  "metric_name": "storage.create",
  "current_value": 0,
  "threshold_value": 0,
  "starts_at": "2024-01-01T10:00:00Z",
  "status": "firing",
  "labels": {
    "event_type": "storage",
    "event_action": "create",
    "event_result": "failed"
  },
  "annotations": {
    "message": "存储节点创建失败",
    "details": {
      "error": "连接超时",
      "request_method": "POST",
      "request_path": "/api/storages"
    }
  }
}
```

## 通知配置

事件告警支持多种通知方式：

### 1. 邮件通知
```json
{
  "type": "email",
  "config": {
    "recipients": ["admin@example.com"],
    "subject_template": "事件告警: {alert_name}",
    "body_template": "事件 {event_type}.{event_action} 失败: {message}"
  }
}
```

### 2. Webhook通知
```json
{
  "type": "webhook",
  "config": {
    "url": "https://api.example.com/webhook",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

### 3. 钉钉通知
```json
{
  "type": "dingtalk",
  "config": {
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "secret": "secret_key"
  }
}
```

## 最佳实践

### 1. 事件记录
- 在所有重要的API接口上使用事件记录装饰器
- 确保事件消息清晰明确
- 在事件详情中包含足够的上下文信息

### 2. 告警策略配置
- 根据业务重要性设置合适的告警级别
- 使用频率限制避免告警风暴
- 定期检查和调整告警策略

### 3. 通知配置
- 配置多种通知方式确保告警能够及时送达
- 根据告警级别设置不同的通知策略
- 定期测试通知配置

### 4. 监控和维护
- 定期查看事件统计和告警统计
- 及时清理旧的事件数据
- 监控告警系统的性能

## 故障排除

### 1. 事件未记录
- 检查路由是否正确使用了事件记录装饰器
- 确认用户已登录且用户ID正确
- 查看应用日志中的错误信息

### 2. 告警未触发
- 检查告警策略是否启用
- 确认事件类型、动作、结果匹配策略配置
- 检查频率限制设置

### 3. 通知未发送
- 检查通知配置是否正确
- 确认通知目标可用
- 查看通知服务的日志

### 4. 性能问题
- 定期清理旧事件数据
- 优化事件查询的索引
- 监控数据库性能

## 扩展开发

### 1. 添加新的事件类型
1. 在 `Event` 模型中添加新的事件类型常量
2. 创建对应的事件记录装饰器
3. 在相关路由中使用新的事件记录装饰器

### 2. 添加新的通知方式
1. 在 `NotificationService` 中添加新的通知方法
2. 在通知配置中支持新的通知类型
3. 更新通知发送逻辑

### 3. 自定义告警评估逻辑
1. 在 `AlertEvaluator` 中添加自定义的评估方法
2. 在告警策略配置中支持自定义规则
3. 更新事件告警评估流程 