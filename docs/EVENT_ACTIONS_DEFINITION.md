# 事件动作定义文档

## 概述

本文档详细定义了 EasySync 系统中所有的事件类型和对应的动作，这些事件动作用于事件告警策略的配置。

## 事件类型定义

### 1. 用户资源 (user)

用户相关的操作事件，包括用户账户管理、认证等操作。

**事件动作：**

- `login` - 用户登录
- `logout` - 用户登出
- `change_password` - 修改密码
- `reset_password` - 重置密码
- `change_email` - 修改邮箱
- `update_profile` - 修改个人信息
- `register` - 用户注册
- `delete_user` - 删除用户
- `change_permission` - 用户权限变更
- `lock_user` - 用户锁定
- `unlock_user` - 用户解锁

**使用场景：**

- 监控异常登录行为
- 监控用户权限变更
- 监控账户安全事件

### 2. 存储资源 (storage)

存储相关的操作事件，包括存储配置管理、连接状态等。

**事件动作：**

- `add_storage` - 添加存储
- `delete_storage` - 删除存储
- `update_storage` - 更新存储
- `test_storage_connection` - 测试存储连通性
- `get_storage_info` - 获取存储信息
- `storage_disconnected` - 存储失联
- `storage_reconnected` - 存储恢复
- `storage_space_low` - 存储空间不足
- `storage_mount` - 存储挂载
- `storage_unmount` - 存储卸载
- `storage_sync` - 存储同步

**使用场景：**

- 监控存储连接状态
- 监控存储空间使用情况
- 监控存储操作失败

### 3. 同步代理资源 (agent)

同步代理相关的操作事件，包括代理生命周期管理。

**事件动作：**

- `agent_start` - 代理启动
- `agent_stop` - 代理停止
- `agent_restart` - 代理重启
- `agent_connect` - 代理连接
- `agent_disconnect` - 代理断开
- `agent_error` - 代理错误
- `agent_upgrade` - 代理升级
- `agent_config_update` - 代理配置更新
- `agent_heartbeat` - 代理心跳

**使用场景：**

- 监控代理运行状态
- 监控代理连接状态
- 监控代理升级过程

### 4. 客户端资源 (client)

客户端相关的操作事件，包括客户端管理、连接状态等。

**事件动作：**

- `client_connect` - 客户端连接
- `client_disconnect` - 客户端断开
- `client_error` - 客户端错误
- `client_timeout` - 客户端超时
- `client_auth_failed` - 客户端认证失败
- `client_add` - 客户端添加
- `client_delete` - 客户端删除
- `client_update` - 客户端更新
- `client_agent_install` - 客户端代理安装
- `client_agent_uninstall` - 客户端代理卸载
- `client_agent_upgrade` - 客户端代理升级
- `client_heartbeat` - 客户端心跳

**使用场景：**

- 监控客户端连接状态
- 监控客户端代理状态
- 监控客户端操作失败

### 5. 监控资源 (monitor)

监控相关的操作事件，包括监控策略管理、数据收集等。

**事件动作：**

- `monitor_data_collect` - 监控数据收集
- `monitor_alert_trigger` - 监控告警触发
- `monitor_alert_resolve` - 监控告警恢复
- `monitor_service_error` - 监控服务异常
- `monitor_threshold_set` - 监控阈值设置
- `monitor_policy_create` - 监控策略创建
- `monitor_policy_update` - 监控策略更新
- `monitor_policy_delete` - 监控策略删除

**使用场景：**

- 监控监控系统本身的状态
- 监控告警策略的变更
- 监控监控服务的异常

### 6. 任务资源 (task)

任务相关的操作事件，包括任务生命周期管理。

**事件动作：**

- `task_create` - 任务创建
- `task_start` - 任务启动
- `task_complete` - 任务完成
- `task_fail` - 任务失败
- `task_pause` - 任务暂停
- `task_resume` - 任务恢复
- `task_cancel` - 任务取消
- `task_delete` - 任务删除
- `task_retry` - 任务重试
- `task_assign` - 任务分配
- `task_progress_update` - 任务进度更新
- `task_config_update` - 任务配置更新

**使用场景：**

- 监控任务执行状态
- 监控任务失败情况
- 监控任务执行效率

### 7. 系统资源 (system)

系统相关的操作事件，包括系统维护、配置管理等。

**事件动作：**

- `system_start` - 系统启动
- `system_shutdown` - 系统关闭
- `system_restart` - 系统重启
- `system_error` - 系统错误
- `system_maintenance` - 系统维护
- `config_update` - 配置更新
- `database_backup` - 数据库备份
- `database_restore` - 数据库恢复
- `log_cleanup` - 日志清理
- `system_upgrade` - 系统升级

**使用场景：**

- 监控系统运行状态
- 监控系统维护操作
- 监控系统升级过程

### 8. 节点资源 (node)

节点相关的操作事件，包括节点管理、连接状态等。

**事件动作：**

- `node_add` - 节点添加
- `node_delete` - 节点删除
- `node_update` - 节点更新
- `node_connect` - 节点连接
- `node_disconnect` - 节点断开
- `node_heartbeat` - 节点心跳
- `node_agent_install` - 节点代理安装
- `node_agent_uninstall` - 节点代理卸载
- `node_agent_upgrade` - 节点代理升级
- `node_group_change` - 节点分组变更

**使用场景：**

- 监控节点连接状态
- 监控节点代理状态
- 监控节点管理操作

## 事件结果定义

### 事件结果类型

- `success` - 成功：操作执行成功
- `failed` - 失败：操作执行失败
- `timeout` - 超时：操作执行超时
- `error` - 错误：操作执行错误
- `warning` - 警告：操作执行警告
- `running` - 进行中：操作正在执行中
- `cancelled` - 已取消：操作已被取消
- `partial_success` - 部分成功：操作部分成功

## 告警策略配置示例

### 1. 用户登录失败告警

```json
{
  "name": "用户登录失败告警",
  "policy_type": "event",
  "event_type": "user",
  "event_actions": ["login"],
  "event_results": ["failed", "error", "timeout"],
  "level": "warning",
  "enabled": true
}
```

### 2. 存储连接失败告警

```json
{
  "name": "存储连接失败告警",
  "policy_type": "event",
  "event_type": "storage",
  "event_actions": ["test_storage_connection", "add_storage", "update_storage"],
  "event_results": ["failed", "error", "timeout"],
  "level": "error",
  "enabled": true
}
```

### 3. 任务执行失败告警

```json
{
  "name": "任务执行失败告警",
  "policy_type": "event",
  "event_type": "task",
  "event_actions": ["task_start", "task_complete"],
  "event_results": ["failed", "error"],
  "level": "error",
  "enabled": true
}
```

### 4. 客户端连接异常告警

```json
{
  "name": "客户端连接异常告警",
  "policy_type": "event",
  "event_type": "client",
  "event_actions": ["client_connect", "client_disconnect", "client_error"],
  "event_results": ["failed", "error", "timeout"],
  "level": "warning",
  "enabled": true
}
```

### 5. 代理状态异常告警

```json
{
  "name": "代理状态异常告警",
  "policy_type": "event",
  "event_type": "agent",
  "event_actions": ["agent_start", "agent_stop", "agent_error"],
  "event_results": ["failed", "error"],
  "level": "error",
  "enabled": true
}
```

## 事件创建示例

### 1. 创建用户登录事件

```python
from backend.app.events.service import event_service

event = event_service.create_user_event(
    user_id=user_id,
    event_action="login",
    event_result="success",
    message="用户登录成功",
    details={"ip": "192.168.1.100", "user_agent": "Mozilla/5.0"}
)
```

### 2. 创建存储连接事件

```python
event = event_service.create_storage_event(
    user_id=user_id,
    event_action="test_storage_connection",
    event_result="failed",
    message="存储连接测试失败",
    details={"storage_name": "test-storage", "error": "connection timeout"}
)
```

### 3. 创建任务执行事件

```python
event = event_service.create_task_event(
    user_id=user_id,
    event_action="task_start",
    event_result="success",
    message="任务开始执行",
    details={"task_id": "task-123", "task_name": "数据同步任务"}
)
```

## 扩展说明

### 添加新的事件类型

1. 在 `AlertEventType` 表中添加新的事件类型
2. 在 `AlertEventAction` 表中添加对应的事件动作
3. 在 `EventService` 中添加创建事件的方法
4. 在业务代码中调用相应的事件创建方法

### 添加新的事件动作

1. 在 `AlertEventAction` 表中添加新的事件动作
2. 在业务代码中创建对应的事件

### 添加新的事件结果

1. 在 `AlertEventResult` 表中添加新的事件结果
2. 在业务代码中使用新的事件结果

## 注意事项

1. 事件动作代码必须唯一
2. 事件结果代码必须唯一
3. 事件类型代码必须唯一
4. 创建事件时确保提供完整的上下文信息
5. 事件告警策略支持频率限制，避免告警风暴
6. 事件告警策略支持持续时间检查
7. 事件告警策略支持去重机制
