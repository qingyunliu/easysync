# 告警系统功能说明

## 概述

根据您的设计需求，我已经重新实现了告警和通知系统，包含以下三个核心模块：

1. **告警策略** - 定义资源告警和事件告警
2. **通知对象** - 关联告警器和通知渠道
3. **通知渠道** - 支持多种通知方式

## 功能架构

### 1. 告警策略 (Alert Policies)

#### 资源告警
- **告警器名称**: 自定义告警器名称
- **级别**: info、warning、error、critical
- **启动状态**: 启用/禁用
- **资源类型**: Nodes、Clients、系统
- **监控资源**: 根据资源类型自动列出可监控的资源
- **报警条目**: CPU、内存、磁盘、网络等
- **触发规则**: 设置阈值、操作符、持续时间
- **通知对象**: 关联已创建的通知对象
- **告警器描述**: 详细描述

#### 事件告警
- **告警器名称**: 自定义告警器名称
- **级别**: info、warning、error、critical
- **启动状态**: 启用/禁用
- **事件类型**: 存储、客户端、代理等
- **事件动作**: 创建、删除、获取等
- **事件结果**: 成功、失败、超时、错误、警告
- **通知对象**: 关联已创建的通知对象
- **告警器描述**: 详细描述

### 2. 通知对象 (Notification Targets)

- **通知对象名称**: 自定义名称
- **启动状态**: 启用/禁用
- **告警器**: 选择关联的告警器
- **发送通道**: 设置好的通知渠道
- **通知对象类型**: 邮件、短信、WebHook等
- **通知配置**: 根据类型配置具体参数
- **描述**: 详细描述

### 3. 通知渠道 (Notification Channels)

- **渠道名称**: 自定义渠道名称
- **渠道类型**: 邮件、短信、WebHook、钉钉、Slack
- **启动状态**: 启用/禁用
- **渠道配置**: 根据类型配置具体参数
- **重试发送次数**: 发送失败时的重试次数
- **速率限制**: 每小时最大发送次数
- **超时时间**: 发送超时时间
- **默认设置**: 是否设为默认渠道

## 数据模型

### AlertPolicy (告警策略)
```python
class AlertPolicy(BaseModel):
    name = db.Column(db.String(100), nullable=False)  # 告警器名称
    description = db.Column(db.Text)  # 告警器描述
    level = db.Column(db.String(20), default='warning')  # 告警级别
    enabled = db.Column(db.Boolean, default=True)  # 启动状态
    policy_type = db.Column(db.String(20), nullable=False)  # 策略类型: resource, event
    
    # 资源告警配置
    resource_type = db.Column(db.String(50))  # 资源类型
    monitored_resources = db.Column(db.JSON)  # 监控资源列表
    alert_items = db.Column(db.JSON)  # 报警条目
    trigger_rules = db.Column(db.JSON)  # 触发规则配置
    
    # 事件告警配置
    event_type = db.Column(db.String(50))  # 事件类型
    event_actions = db.Column(db.JSON)  # 事件动作
    event_results = db.Column(db.JSON)  # 事件结果
    
    # 通知配置
    notification_targets = db.Column(db.JSON)  # 关联的通知对象ID列表
```

### NotificationChannel (通知渠道)
```python
class NotificationChannel(BaseModel):
    name = db.Column(db.String(100), nullable=False)  # 渠道名称
    channel_type = db.Column(db.String(50), nullable=False)  # 渠道类型
    enabled = db.Column(db.Boolean, default=True)  # 启动状态
    config = db.Column(db.JSON, nullable=False)  # 渠道配置
    retry_count = db.Column(db.Integer, default=3)  # 重试发送次数
    rate_limit = db.Column(db.Integer, default=100)  # 速率限制
    timeout = db.Column(db.Integer, default=30)  # 超时时间
    is_default = db.Column(db.Boolean, default=False)  # 是否设置为默认
```

### NotificationTarget (通知对象)
```python
class NotificationTarget(BaseModel):
    name = db.Column(db.String(100), nullable=False)  # 通知对象名称
    enabled = db.Column(db.Boolean, default=True)  # 启动状态
    description = db.Column(db.Text)  # 描述
    alert_policies = db.Column(db.JSON)  # 关联的告警器ID列表
    channels = db.Column(db.JSON)  # 关联的通知渠道ID列表
    target_type = db.Column(db.String(50), nullable=False)  # 通知对象类型
    target_config = db.Column(db.JSON, nullable=False)  # 通知对象配置
```

## API 接口

### 告警策略接口
- `GET /api/alerts/policies` - 获取告警策略列表
- `POST /api/alerts/policies` - 创建告警策略
- `GET /api/alerts/policies/{id}` - 获取告警策略详情
- `PUT /api/alerts/policies/{id}` - 更新告警策略
- `DELETE /api/alerts/policies/{id}` - 删除告警策略
- `PUT /api/alerts/policies/{id}/toggle` - 切换启用状态
- `POST /api/alerts/policies/{id}/test` - 测试告警策略

### 通知渠道接口
- `GET /api/alerts/channels` - 获取通知渠道列表
- `POST /api/alerts/channels` - 创建通知渠道
- `PUT /api/alerts/channels/{id}` - 更新通知渠道
- `DELETE /api/alerts/channels/{id}` - 删除通知渠道

### 通知对象接口
- `GET /api/alerts/targets` - 获取通知对象列表
- `POST /api/alerts/targets` - 创建通知对象
- `PUT /api/alerts/targets/{id}` - 更新通知对象
- `DELETE /api/alerts/targets/{id}` - 删除通知对象

### 辅助接口
- `GET /api/alerts/resources` - 获取可监控的资源列表
- `GET /api/alerts/events` - 获取可监控的事件列表
- `GET /api/alerts/templates` - 获取告警策略模板

## 前端页面

### 1. 告警策略页面 (`/alert-policies`)
- 支持资源告警和事件告警的创建和管理
- 提供策略模板库
- 支持策略的启用/禁用、编辑、删除、测试
- 显示策略详情和关联信息

### 2. 通知渠道页面 (`/notification-channels`)
- 支持邮件、短信、WebHook、钉钉、Slack等渠道
- 提供渠道配置和测试功能
- 支持设置默认渠道
- 显示渠道状态和配置信息

### 3. 通知对象页面 (`/notification-targets`)
- 支持邮件、短信、WebHook等通知对象类型
- 关联告警器和通知渠道
- 配置具体的通知地址
- 显示关联信息和状态

## 使用流程

### 1. 创建通知渠道
1. 进入"通知渠道"页面
2. 点击"创建渠道"
3. 选择渠道类型（邮件、短信、WebHook等）
4. 配置渠道参数
5. 保存渠道

### 2. 创建通知对象
1. 进入"通知对象"页面
2. 点击"创建通知对象"
3. 选择对象类型
4. 配置通知地址
5. 关联通知渠道
6. 保存对象

### 3. 创建告警策略
1. 进入"告警策略"页面
2. 点击"创建告警器"
3. 选择策略类型（资源告警或事件告警）
4. 配置监控参数和触发规则
5. 关联通知对象
6. 保存策略

## 配置示例

### 邮件渠道配置
```json
{
  "name": "邮件通知",
  "channel_type": "email",
  "config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your@email.com",
    "password": "your_password"
  }
}
```

### 资源告警策略配置
```json
{
  "name": "CPU使用率告警",
  "policy_type": "resource",
  "resource_type": "system",
  "alert_items": ["CPU"],
  "trigger_rules": {
    "CPU": {
      "operator": ">",
      "threshold": 80,
      "duration": 300
    }
  },
  "notification_targets": ["target_id"]
}
```

### 事件告警策略配置
```json
{
  "name": "存储操作失败告警",
  "policy_type": "event",
  "event_type": "storage",
  "event_actions": ["create", "delete", "update"],
  "event_results": ["failed", "error"],
  "notification_targets": ["target_id"]
}
```

### 客户端连接失败告警配置
```json
{
  "name": "客户端连接失败告警",
  "policy_type": "event",
  "event_type": "client",
  "event_actions": ["connect"],
  "event_results": ["failed", "timeout"],
  "notification_targets": ["target_id"]
}
```

## 测试

运行测试脚本验证功能：
```bash
python test_alert_system.py
```

## 注意事项

1. 确保数据库已正确初始化
2. 配置正确的通知渠道参数
3. 测试告警策略前先创建通知对象和渠道
4. 定期检查告警策略的有效性
5. 监控通知发送的成功率

## 扩展功能

未来可以考虑添加的功能：
1. 告警历史记录和统计
2. 告警升级机制
3. 告警抑制和静默
4. 告警聚合和去重
5. 告警仪表板
6. 告警规则模板市场 