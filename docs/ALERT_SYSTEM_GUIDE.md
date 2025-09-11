# 监控告警系统使用指南

## 系统概述

EasySync 的监控告警系统支持两种类型的告警：
- **资源告警**：基于系统资源使用情况（CPU、内存、磁盘、网络等）
- **事件告警**：基于系统事件（存储操作、客户端连接、任务执行等）

## 告警策略配置

### 1. 创建告警策略

#### 资源告警策略示例
```json
{
  "name": "CPU使用率告警",
  "description": "当CPU使用率超过80%时触发告警",
  "policy_type": "resource",
  "resource_type": "System",
  "alert_items": ["CPU"],
  "trigger_rules": {
    "CPU": {
      "operator": ">",
      "threshold": 80,
      "duration": 300
    }
  },
  "level": "warning",
  "notification_targets": ["target_id_1", "target_id_2"],
  "enabled": true
}
```

#### 事件告警策略示例
```json
{
  "name": "存储连接失败告警",
  "description": "当存储连接失败时触发告警",
  "policy_type": "event",
  "event_type": "storage",
  "event_actions": ["connect"],
  "event_results": ["failed"],
  "level": "error",
  "notification_targets": ["target_id_1"],
  "enabled": true
}
```

### 2. 告警策略字段说明

#### 通用字段
- `name`: 策略名称
- `description`: 策略描述
- `policy_type`: 策略类型（"resource" 或 "event"）
- `level`: 告警级别（"info", "warning", "error", "critical"）
- `notification_targets`: 通知目标ID列表
- `enabled`: 是否启用

#### 资源告警字段
- `resource_type`: 资源类型（"System", "Nodes", "Clients"）
- `alert_items`: 监控指标列表（["CPU", "内存", "磁盘", "网络"]）
- `trigger_rules`: 触发规则配置
- `monitored_resources`: 监控的资源ID列表（可选）

#### 事件告警字段
- `event_type`: 事件类型（"storage", "client", "task", "system"等）
- `event_actions`: 事件动作列表（["create", "delete", "connect", "disconnect"]等）
- `event_results`: 事件结果列表（["success", "failed", "timeout"]等）

### 3. 触发规则配置

#### 阈值条件
```json
{
  "operator": ">",  // 操作符：>, >=, <, <=, ==, !=
  "threshold": 80,  // 阈值
  "duration": 300   // 持续时间（秒），0表示立即触发
}
```

#### 频率限制
```json
{
  "frequency_limit": {
    "time_window": 3600,  // 时间窗口（秒）
    "max_count": 10       // 最大次数
  }
}
```

## 通知渠道配置

### 1. 创建通知渠道

#### 邮件渠道
```json
{
  "name": "邮件通知",
  "channel_type": "email",
  "config": {
    "smtp_server": "smtp.example.com",
    "smtp_port": 587,
    "username": "alerts@example.com",
    "password": "password",
    "use_tls": true
  },
  "enabled": true
}
```

#### 钉钉渠道
```json
{
  "name": "钉钉通知",
  "channel_type": "dingtalk",
  "config": {
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "secret": "SECxxx"
  },
  "enabled": true
}
```

#### Webhook渠道
```json
{
  "name": "Webhook通知",
  "channel_type": "webhook",
  "config": {
    "url": "https://api.example.com/webhook",
    "secret": "webhook_secret"
  },
  "enabled": true
}
```

### 2. 创建通知对象

#### 邮件通知对象
```json
{
  "name": "管理员邮件",
  "target_type": "email",
  "target_config": {
    "email": "admin@example.com"
  },
  "channels": ["channel_id_1"],
  "alert_policies": ["policy_id_1", "policy_id_2"],
  "enabled": true
}
```

#### 短信通知对象
```json
{
  "name": "紧急短信",
  "target_type": "sms",
  "target_config": {
    "phone": "13800138000"
  },
  "channels": ["channel_id_2"],
  "alert_policies": ["policy_id_3"],
  "enabled": true
}
```

## 告警模板配置

### 1. 创建告警模板

```json
{
  "name": "默认邮件模板",
  "description": "默认的邮件告警模板",
  "category": "email",
  "template_type": "email",
  "title_template": "[{level}] {alert_name} - {resource_name}",
  "content_template": "告警策略: {policy_name}\n告警级别: {level}\n资源名称: {resource_name}\n当前值: {current_value}\n阈值: {threshold_value}\n触发时间: {triggered_at}\n描述: {description}",
  "variables": ["level", "alert_name", "resource_name", "policy_name", "current_value", "threshold_value", "triggered_at", "description"],
  "is_system": false,
  "enabled": true
}
```

### 2. 模板变量说明

#### 资源告警变量
- `policy_name`: 策略名称
- `level`: 告警级别
- `resource_name`: 资源名称
- `metric_name`: 指标名称
- `current_value`: 当前值
- `threshold_value`: 阈值
- `triggered_at`: 触发时间
- `description`: 描述

#### 事件告警变量
- `policy_name`: 策略名称
- `level`: 告警级别
- `event_type`: 事件类型
- `event_action`: 事件动作
- `event_result`: 事件结果
- `triggered_at`: 触发时间
- `message`: 事件消息
- `details`: 事件详情

## 系统集成

### 1. 监控数据收集

系统会自动收集以下监控数据：
- **系统级监控**：CPU、内存、磁盘、网络使用情况
- **节点监控**：各个代理节点的资源使用情况
- **客户端监控**：客户端连接状态和性能指标

### 2. 事件触发

系统会在以下情况下触发事件：
- 存储操作（创建、删除、连接、断开）
- 客户端操作（连接、断开、注册、注销）
- 任务操作（开始、完成、失败、暂停）
- 系统操作（错误、警告、维护）

### 3. 告警评估

告警评估器会：
1. 检查监控数据是否满足告警策略的触发条件
2. 验证事件是否匹配事件告警策略
3. 检查频率限制，避免告警风暴
4. 创建告警实例并发送通知

## 最佳实践

### 1. 告警策略设计
- 设置合理的阈值，避免误报
- 使用持续时间条件，避免瞬时峰值触发告警
- 设置频率限制，防止告警风暴
- 根据业务重要性设置不同的告警级别

### 2. 通知配置
- 为不同级别的告警配置不同的通知渠道
- 设置免打扰时间，避免在非工作时间发送通知
- 定期测试通知渠道的可用性
- 配置多个通知目标，确保告警能够及时送达

### 3. 监控和维护
- 定期检查告警策略的有效性
- 监控告警系统的性能
- 及时处理告警，避免告警堆积
- 根据业务变化调整告警策略

## 故障排除

### 1. 告警不触发
- 检查告警策略是否启用
- 验证触发条件配置是否正确
- 确认监控数据是否正常收集
- 查看告警评估器日志

### 2. 通知发送失败
- 检查通知渠道配置是否正确
- 验证网络连接是否正常
- 确认通知目标配置是否有效
- 查看通知服务日志

### 3. 告警风暴
- 检查频率限制配置
- 调整告警阈值
- 优化告警策略逻辑
- 增加告警去重机制

## API 接口

### 告警策略管理
- `GET /api/alerts/policies` - 获取告警策略列表
- `POST /api/alerts/policies` - 创建告警策略
- `PUT /api/alerts/policies/{id}` - 更新告警策略
- `DELETE /api/alerts/policies/{id}` - 删除告警策略
- `POST /api/alerts/policies/{id}/test` - 测试告警策略

### 通知渠道管理
- `GET /api/notifications/channels` - 获取通知渠道列表
- `POST /api/notifications/channels` - 创建通知渠道
- `PUT /api/notifications/channels/{id}` - 更新通知渠道
- `DELETE /api/notifications/channels/{id}` - 删除通知渠道
- `POST /api/notifications/channels/{id}/test` - 测试通知渠道

### 告警实例查询
- `GET /api/alerts/instances` - 获取告警实例列表
- `GET /api/alerts/instances/{id}` - 获取告警实例详情
- `POST /api/alerts/instances/{id}/resolve` - 解决告警实例

通过以上配置和使用指南，您可以充分利用 EasySync 的监控告警系统，实现全面的系统监控和告警管理。
