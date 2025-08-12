# 告警系统设计文档

## 概述

EasySync 告警系统支持两种类型的告警：

1. **资源告警** - 监控系统资源（CPU、内存、磁盘、网络等）
2. **事件告警** - 监控系统事件（用户操作、存储操作、任务执行等）

## 系统架构

### 核心组件

1. **告警模型层**

   - `AlertResourceType` - 资源类型定义
   - `AlertResourceItem` - 资源监控条目
   - `AlertEventType` - 事件类型定义
   - `AlertEventAction` - 事件动作定义
   - `AlertEventResult` - 事件结果定义
   - `AlertPolicy` - 告警策略
   - `AlertInstance` - 告警实例
   - `AlertTemplate` - 告警模板

2. **服务层**

   - `AlertService` - 告警服务
   - `AlertEvaluator` - 告警评估器
   - `EventService` - 事件服务

3. **API 层**
   - 告警策略管理 API
   - 事件管理 API
   - 告警实例查询 API

## 资源告警

### 支持的资源类型

1. **系统资源** (`system`)

   - CPU 使用率 - 监控 CPU 使用率百分比
   - 内存使用率 - 监控内存使用率百分比
   - 磁盘使用率 - 监控磁盘使用率百分比
   - 系统负载 - 监控系统平均负载

2. **存储资源** (`storage`)

   - 存储状态 - 监控存储连接状态（active/error/disabled）
   - 存储连接时间 - 监控存储连接响应时间
   - 存储可用空间 - 监控存储可用空间百分比

3. **网络资源** (`network`)

   - 网络延迟 - 监控网络延迟时间
   - 网络连接数 - 监控当前网络连接数

4. **客户端资源** (`client`)

   - 客户端连接状态 - 监控客户端连接状态（online/offline）
   - 客户端代理状态 - 监控客户端代理运行状态（active/inactive/error）
   - 客户端响应时间 - 监控客户端响应时间
   - 客户端最后心跳时间 - 监控客户端最后心跳时间间隔

5. **节点资源** (`node`)
   - 节点状态 - 监控同步节点运行状态（online/offline/error）
   - 代理状态 - 监控节点代理运行状态（active/inactive/error）
   - 任务执行数量 - 监控当前执行的任务数量
   - 节点最后心跳时间 - 监控节点最后心跳时间间隔

### 配置示例

```json
{
  "name": "CPU告警策略",
  "policy_type": "resource",
  "resource_type": "system",
  "alert_items": ["cpu_percent"],
  "trigger_rules": {
    "cpu_percent": {
      "operator": ">",
      "threshold": 80.0,
      "duration": 300
    }
  },
  "level": "warning",
  "enabled": true
}
```

## 事件告警

### 支持的事件类型

1. **用户资源** (`user`)

   - 登录、登出、修改密码、重置密码、修改邮箱、修改个人信息
   - 用户注册、删除用户、用户权限变更、用户锁定、用户解锁

2. **存储资源** (`storage`)

   - 添加、删除、更新存储，测试存储连通性，获取存储信息
   - 存储失联、存储恢复、存储空间不足、存储挂载、存储卸载、存储同步

3. **同步代理资源** (`agent`)

   - 代理启动、停止、重启、连接、断开、错误、升级
   - 代理配置更新、代理心跳

4. **客户端资源** (`client`)

   - 客户端连接、断开、错误、超时、认证失败
   - 客户端添加、删除、更新、代理安装/卸载/升级、客户端心跳

5. **监控资源** (`monitor`)

   - 监控数据收集、监控告警触发/恢复、监控服务异常
   - 监控阈值设置、监控策略创建/更新/删除

6. **任务资源** (`task`)

   - 任务创建、启动、完成、失败、暂停、恢复、取消、删除
   - 任务重试、任务分配、任务进度更新、任务配置更新

7. **系统资源** (`system`)

   - 系统启动、关闭、重启、错误、维护
   - 配置更新、数据库备份/恢复、日志清理、系统升级

8. **节点资源** (`node`)
   - 节点添加、删除、更新、连接、断开、心跳
   - 节点代理安装/卸载/升级、节点分组变更

### 事件结果

- `success` - 成功
- `failed` - 失败
- `timeout` - 超时
- `error` - 错误
- `warning` - 警告
- `running` - 进行中
- `cancelled` - 已取消
- `partial_success` - 部分成功

### 配置示例

```json
{
  "name": "存储操作失败告警",
  "policy_type": "event",
  "event_type": "storage",
  "event_actions": ["add_storage", "delete_storage", "update_storage"],
  "event_results": ["failed", "error"],
  "level": "error",
  "enabled": true
}
```

## API 接口

### 告警策略管理

- `GET /api/alerts/policies` - 获取告警策略列表
- `POST /api/alerts/policies` - 创建告警策略
- `GET /api/alerts/policies/{id}` - 获取策略详情
- `PUT /api/alerts/policies/{id}` - 更新策略
- `DELETE /api/alerts/policies/{id}` - 删除策略
- `PUT /api/alerts/policies/{id}/toggle` - 切换启用状态

### 告警分类管理

- `GET /api/alerts/categories` - 获取告警分类信息
- `GET /api/alerts/resource-types` - 获取资源类型
- `GET /api/alerts/resource-items` - 获取资源条目
- `GET /api/alerts/event-types` - 获取事件类型
- `GET /api/alerts/event-actions` - 获取事件动作
- `GET /api/alerts/event-results` - 获取事件结果

### 事件管理

- `GET /api/events/list` - 获取事件列表
- `POST /api/events/create` - 创建事件
- `POST /api/events/user` - 创建用户事件
- `POST /api/events/storage` - 创建存储事件
- `POST /api/events/agent` - 创建代理事件
- `POST /api/events/client` - 创建客户端事件
- `POST /api/events/task` - 创建任务事件
- `POST /api/events/system` - 创建系统事件

### 告警实例管理

- `GET /api/alerts/instances` - 获取告警实例列表
- `PUT /api/alerts/instances/{id}/resolve` - 解决告警实例

## 使用示例

### 1. 创建资源告警策略

```python
from backend.app.alerts.services import AlertService

alert_service = AlertService()

policy_data = {
    "name": "内存使用率告警",
    "description": "监控系统内存使用率",
    "policy_type": "resource",
    "resource_type": "system",
    "alert_items": ["memory_percent"],
    "trigger_rules": {
        "memory_percent": {
            "operator": ">",
            "threshold": 85.0,
            "duration": 60
        }
    },
    "level": "warning",
    "enabled": True
}

policy = alert_service.create_policy(policy_data, user_id)
```

### 2. 创建事件告警策略

```python
policy_data = {
    "name": "存储操作失败告警",
    "description": "监控存储操作失败事件",
    "policy_type": "event",
    "event_type": "storage",
    "event_actions": ["add_storage", "delete_storage"],
    "event_results": ["failed", "error"],
    "level": "error",
    "enabled": True
}

policy = alert_service.create_policy(policy_data, user_id)
```

### 3. 创建事件

```python
from backend.app.events.service import event_service

# 创建存储事件
event = event_service.create_storage_event(
    user_id=user_id,
    event_action="add_storage",
    event_result="failed",
    message="添加存储失败：连接超时",
    details={"storage_name": "test-storage", "error": "connection timeout"}
)
```

## 部署说明

### 1. 创建数据库表

```bash
cd migrations
python create_alert_tables.py
```

### 2. 初始化基础数据

系统会自动初始化以下基础数据：

- 资源类型和条目
- 事件类型和动作
- 事件结果类型
- 系统默认模板

### 3. 配置告警策略

用户可以通过 Web 界面或 API 配置告警策略：

1. 选择告警类型（资源/事件）
2. 配置监控条件
3. 设置告警级别
4. 关联通知模板
5. 配置通知目标

## 监控和告警流程

1. **数据收集** - 系统收集监控数据和事件
2. **策略评估** - 告警评估器检查是否触发策略
3. **实例创建** - 创建告警实例
4. **通知发送** - 根据配置发送通知
5. **状态管理** - 管理告警状态（触发/解决）

## 扩展性

系统设计具有良好的扩展性：

1. **新增资源类型** - 在`AlertResourceType`表中添加
2. **新增监控条目** - 在`AlertResourceItem`表中添加
3. **新增事件类型** - 在`AlertEventType`表中添加
4. **新增事件动作** - 在`AlertEventAction`表中添加
5. **自定义通知模板** - 支持多种通知渠道

## 注意事项

1. 告警策略支持频率限制，避免告警风暴
2. 事件告警支持持续时间检查
3. 告警实例支持去重机制
4. 系统提供告警统计和分析功能
5. 支持告警模板的变量替换
