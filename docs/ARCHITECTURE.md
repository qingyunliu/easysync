# EasySync 通知和告警架构设计

## 模块职责分工

### 1. Notifications 模块 (`backend/app/notifications/`)
**职责：通知的发送和接收**

#### 核心功能：
- ✅ **通知创建和存储**：创建系统通知，存储到数据库
- ✅ **通知发送**：通过多种渠道发送通知（邮件、Webhook、钉钉、短信）
- ✅ **通知管理**：标记已读、删除通知、获取通知列表
- ✅ **通知策略**：根据用户设置过滤通知
- ✅ **免打扰时间**：检查是否在免打扰时间内
- ✅ **外部通知**：发送邮件、Webhook等外部通知

#### 主要组件：
- `NotificationService`：通知服务核心类
- `Notification`：通知数据模型
- `NotificationSetting`：用户通知设置模型
- `routes.py`：通知相关API接口

#### API接口：
- `GET /api/notifications/list`：获取通知列表
- `POST /api/notifications/<id>/read`：标记通知已读
- `DELETE /api/notifications/<id>`：删除通知
- `GET /api/notifications/config`：获取通知配置
- `POST /api/notifications/config`：保存通知配置
- `POST /api/notifications/test`：测试通知发送

### 2. Alerts 模块 (`backend/app/alerts/`)
**职责：告警策略管理和告警触发**

#### 核心功能：
- ✅ **告警策略管理**：创建、更新、删除告警策略
- ✅ **告警规则管理**：定义告警触发条件和阈值
- ✅ **告警触发**：根据策略触发告警
- ✅ **告警解决**：标记告警为已解决
- ✅ **通知渠道管理**：管理不同的通知渠道配置
- ✅ **告警实例管理**：记录告警实例和状态

#### 主要组件：
- `AlertPolicyService`：告警策略服务类
- `AlertPolicy`：告警策略模型
- `AlertPolicyRule`：告警规则模型
- `AlertInstance`：告警实例模型
- `NotificationChannel`：通知渠道模型
- `routes.py`：告警相关API接口

#### API接口：
- `GET /api/alerts/policies`：获取告警策略列表
- `POST /api/alerts/policies`：创建告警策略
- `PUT /api/alerts/policies/<id>`：更新告警策略
- `DELETE /api/alerts/policies/<id>`：删除告警策略
- `GET /api/alerts/notification-channels`：获取通知渠道列表
- `POST /api/alerts/notification-channels`：创建通知渠道
- `POST /api/alerts/notification-channels/<id>/test`：测试通知渠道

### 3. Monitor 模块 (`backend/app/monitor/`)
**职责：监控数据收集和告警检测**

#### 核心功能：
- ✅ **监控数据收集**：收集系统、节点、客户端的监控数据
- ✅ **告警检测**：根据告警策略检测异常情况
- ✅ **告警触发**：调用alerts模块触发告警
- ✅ **监控统计**：提供监控数据统计和分析

#### 主要组件：
- `MonitorService`：监控服务类
- `MonitorData`：监控数据模型
- `AlertRule`：告警规则模型（与alerts模块共享）

## 数据流向

```
监控数据 → Monitor模块 → 告警检测 → Alerts模块 → 触发告警 → Notifications模块 → 发送通知
```

### 详细流程：

1. **Monitor模块**收集监控数据
2. **Monitor模块**根据告警规则检测异常
3. **Monitor模块**调用`AlertPolicyService.trigger_alert()`触发告警
4. **Alerts模块**创建告警实例
5. **Alerts模块**调用`NotificationService.send_notification()`发送通知
6. **Notifications模块**根据用户设置发送通知到各个渠道

## 代码复用和依赖关系

### 依赖关系：
```
Monitor模块 → Alerts模块 → Notifications模块
```

### 代码复用：
- **Alerts模块**复用**Notifications模块**的通知发送功能
- **Monitor模块**复用**Alerts模块**的告警策略管理功能
- 避免重复实现通知发送逻辑

### 接口设计：
- **Notifications模块**提供`send_notification()`方法供其他模块调用
- **Alerts模块**提供`trigger_alert()`和`resolve_alert()`方法供Monitor模块调用
- 各模块通过明确的接口进行通信，避免紧耦合

## 配置管理

### 通知配置：
- 用户级别的通知设置（`NotificationSetting`）
- 支持邮件、Webhook、钉钉、短信等多种渠道
- 支持免打扰时间和通知策略

### 告警配置：
- 告警策略配置（`AlertPolicy`）
- 告警规则配置（`AlertPolicyRule`）
- 通知渠道配置（`NotificationChannel`）

## 扩展性设计

### 新增通知渠道：
1. 在`NotificationService`中添加新的发送方法
2. 在`NotificationSetting`中添加新的配置字段
3. 在前端添加相应的配置界面

### 新增告警类型：
1. 在`AlertPolicy`中添加新的告警类型
2. 在`MonitorService`中添加相应的检测逻辑
3. 在前端添加相应的配置界面

### 新增监控指标：
1. 在`MonitorData`中添加新的指标字段
2. 在`MonitorService`中添加数据收集逻辑
3. 在告警规则中支持新的指标

## 最佳实践

### 1. 模块职责清晰：
- Notifications模块专注于通知发送
- Alerts模块专注于告警策略管理
- Monitor模块专注于监控数据收集

### 2. 避免重复实现：
- 通知发送逻辑只在Notifications模块中实现
- 告警策略管理逻辑只在Alerts模块中实现
- 监控数据收集逻辑只在Monitor模块中实现

### 3. 接口设计：
- 模块间通过明确的接口进行通信
- 避免直接访问其他模块的内部实现
- 使用依赖注入的方式管理模块依赖

### 4. 错误处理：
- 每个模块都有完善的错误处理机制
- 错误信息通过日志记录，便于调试
- 用户友好的错误提示

### 5. 性能优化：
- 使用异步处理大量通知发送
- 合理使用数据库索引
- 缓存常用的配置信息 