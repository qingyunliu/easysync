# 一、核心功能模块与实现建议

## 1. 资源管理

### 1.1 Clients（源端主机）

- 仅作为同步"源"，由本地 agent 执行同步任务。
- 需支持：注册、心跳、状态监控、详情、分组/标签、批量管理。

### 1.2 Storages（存储资源）

- 既可为"源"也可为"目标"，支持多类型（NAS、NFS、OBS、S3、本地等）。
- 需支持：增删查改、挂载检测、连接测试、分组/标签、批量管理。

### 1.3 Nodes（同步代理/Proxy）

- 仅用于 Storage ↔ Storage 场景，负责挂载和同步。
- 需支持：注册、心跳、健康检查、任务分发、状态监控、分组/标签。

## 2. 同步任务编排

### 2.1 任务模型

- 字段建议：任务 ID、名称、源类型（Client/Storage）、源 ID、目标类型（Storage）、目标 ID、执行节点（Client agent/Node proxy）、同步策略（全量/增量/定时/实时/手动）、过滤规则、优先级、状态、进度、日志等。

### 2.2 任务调度逻辑

- 源为 Client 时，任务下发给 Client agent。
- 源为 Storage 时，任务下发给 Node proxy。
- 需支持：任务创建、编辑、删除、调度、状态查询、进度展示、失败重试。

## 3. 监控与日志

### 3.1 监控

- Client/Node/Storage 状态监控（心跳、资源占用、挂载状态等）。
- 任务执行进度、速率、剩余时间、失败项统计。

### 3.2 日志

- 任务执行日志、系统操作日志、审计日志。
- 支持分级、搜索、导出、保留策略。

## 4. 用户与权限

- 多用户、RBAC 权限、操作审计、登录安全。
- 用户可见/可操作的资源隔离。

# 二、数据模型建议（简化版）

- **clients**：`id`, `name`, `ip`, `group`, `tags`, `status`, `last_heartbeat`, ...
- **storages**：`id`, `name`, `type`, `config`, `group`, `tags`, `status`, ...
- `nodes`：`id`, `name`, `ip`, `group`, `tags`, `status`, `last_heartbeat`, ...
- **tasks**：`id`, `name`, `src_type`, `src_id`, `dst_type`, `dst_id`, `executor_type`, `executor_id`, `schedule`, `filter`, `priority`, `status`, `progress`, ...
- **logs**：`id`, `task_id`, `level`, `message`, `timestamp`, ...
- **users/roles/permissions**：略

# 三、API 接口设计（RESTful 风格）

## 1. Clients

- `GET /api/clients`：获取列表
- `POST /api/clients`：新增
- `GET /api/clients/<id>`：详情
- `PUT /api/clients/<id>`：编辑
- `DELETE /api/clients/<id>`：删除
- `POST /api/clients/heartbeat`：心跳

## 2. Storages

- `GET /api/storages`
- `POST /api/storages`
- `GET /api/storages/<id>`
- `PUT /api/storages/<id>`
- `DELETE /api/storages/<id>`
- `POST /api/storages/test`：连接测试

## 3. Nodes

- `GET /api/nodes`
- `POST /api/nodes`
- `GET /api/nodes/<id>`
- `PUT /api/nodes/<id>`
- `DELETE /api/nodes/<id>`
- `POST /api/nodes/heartbeat`：心跳

## 4. Tasks

- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/<id>`
- `PUT /api/tasks/<id>`
- `DELETE /api/tasks/<id>`
- `POST /api/tasks/<id>/start`
- `POST /api/tasks/<id>/stop`
- `GET /api/tasks/<id>/progress`
- `GET /api/tasks/<id>/logs`

## 5. 日志与监控

- `GET /api/logs`
- `GET /api/audit_logs`
- `GET /api/monitor/clients/<id>`
- `GET /api/monitor/nodes/<id>`

## 6. 用户与权限

- `POST /api/login`
- `GET /api/users`
- `POST /api/users`
- ...

# 四、前端交互建议

- 任务创建页面：根据"源类型"动态限制"目标类型"与"执行节点"选择。
- 资源管理页面：支持分组、标签、批量操作、状态筛选。
- 监控面板：实时展示节点/任务状态，支持异常告警。
- 日志中心：支持多维度检索、导出。

# 五、开发任务拆解（建议逐条推进）

## 资源管理

- [ ] 完善 Clients 增删查改、心跳、分组/标签
- [ ] 完善 Storages 增删查改、挂载检测、连接测试
- [ ] 完善 Nodes 增删查改、心跳、健康检查

## 任务系统

- [ ] 设计并实现任务数据模型
- [ ] 任务创建/编辑/删除/调度接口
- [ ] 任务调度逻辑（区分 Client/Node 执行）
- [ ] 任务进度、状态、日志接口

## 监控与日志

- [ ] 节点/任务监控 API
- [ ] 日志/审计 API

## 权限与用户

- [ ] 用户/角色/权限管理
- [ ] 操作审计

## 前端联动

- [ ] 任务创建/编辑页面联动逻辑
- [ ] 资源管理、监控、日志等页面完善

# 六、建议的开发顺序

先把资源管理（Clients/Storages/Nodes）和任务模型/接口打通，保证任务能完整流转。
再完善监控、日志、权限等增强功能。
最后做前端交互优化和批量操作、分组、标签、告警等细节。

# 六、Agent 与 Proxy 程序开发规划

## 1. EasySync-Agent（源端同步客户端）

**定位**：部署在用户源端主机（Clients）上的轻量级同步客户端，负责本地数据采集、同步任务执行、状态/监控上报。

**核心功能**：

- 注册与心跳：启动时向主控注册，定期心跳上报状态与监控数据
- 任务拉取与执行：定时拉取分配给本机的同步任务，支持全量/增量同步、失败重试、进度回报
- 本地数据采集：采集指定目录/文件的变更，支持过滤规则
- 日志与监控：本地执行日志、同步进度、资源占用等实时上报
- 安全与权限：支持 Token 鉴权、最小权限原则
- 自升级机制：支持远程下发升级指令，自动拉取新版本

**数据流与 API 交互**：

- 启动注册 → `POST /api/agent/register`
- 定时心跳 → `POST /api/agent/heartbeat`
- 拉取任务 → `GET /api/agent/<client_id>/tasks`
- 上报结果 → `POST /api/agent/<client_id>/tasks/<task_id>/report`
- 获取配置/升级 → `GET /api/agent/<client_id>/config`

**部署建议**：

- 支持 Linux 主流发行版，推荐以 systemd 服务方式运行
- 轻量依赖，支持 Python/Go 多语言实现
- 提供一键安装脚本与自动注册命令

**与主系统关系**：

- 仅作为"源端"数据采集与同步执行者，不作为目标
- 通过 API 与主控系统解耦，便于弹性扩展

---

## 2. EasySync-Proxy（同步代理节点）

**定位**：部署在中立主机上的同步代理，负责 Storage↔Storage（如 NAS↔NAS、NAS↔OBS 等）场景下的同步任务执行与资源挂载。

**核心功能**：

- 注册与心跳：启动时向主控注册，定期心跳上报状态与资源监控
- 存储挂载管理：自动挂载/检测源端与目标端存储（NFS、NAS、OBS 等）
- 任务拉取与执行：定时拉取分配给本节点的同步任务，负责数据搬运
- 同步引擎集成：集成 rsync/rclone 等工具，支持多协议、多厂商
- 日志与监控：同步过程日志、资源占用、挂载状态等实时上报
- 故障自愈与切换：支持挂载异常自动重试、任务转移
- 安全与权限：支持 Token 鉴权、最小权限原则
- 插件扩展：预留插件机制，便于后续扩展新存储类型

**数据流与 API 交互**：

- 启动注册 → `POST /api/nodes/register`
- 定时心跳 → `POST /api/nodes/heartbeat`
- 拉取任务 → `GET /api/nodes/<node_id>/tasks`
- 上报结果 → `POST /api/nodes/<node_id>/tasks/<task_id>/report`
- 获取配置/升级 → `GET /api/nodes/<node_id>/config`

**部署建议**：

- 推荐部署在有良好网络与存储访问能力的中立主机
- 支持多实例部署，实现负载均衡与高可用
- 提供一键安装与自动注册脚本

**与主系统关系**：

- 作为 Storage↔Storage 同步的执行代理，承担数据搬运与挂载管理
- 通过 API 与主控系统解耦，支持弹性扩展与故障转移

---
