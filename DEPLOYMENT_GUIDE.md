# EasySync 完整系统部署指南

## 系统概述

EasySync 是一个完整的数据同步平台，支持多种存储类型的数据同步，包含前端管理界面、后端API服务和分布式代理节点。

### 核心功能

#### 🎯 任务管理
- ✅ **任务创建**：支持存储到存储、客户端到存储的同步任务
- ✅ **任务启动/停止**：完整的任务生命周期管理
- ✅ **任务暂停/恢复**：支持任务的暂停和恢复操作
- ✅ **任务取消**：优雅的任务取消机制
- ✅ **任务重试**：智能重试机制，支持指数退避
- ✅ **任务删除**：支持强制删除运行中的任务
- ✅ **批量操作**：支持批量任务管理

#### 🔧 连接测试和诊断
- ✅ **存储连接测试**：支持NAS、NFS、S3、本地存储的连接测试
- ✅ **挂载测试**：NFS/SMB挂载状态检查和测试
- ✅ **网络诊断**：网络连接和延迟测试
- ✅ **自动故障诊断**：详细的错误分类和处理建议

#### 📊 实时监控和统计
- ✅ **任务统计面板**：实时显示任务状态统计
- ✅ **进度跟踪**：详细的任务进度和传输速度监控
- ✅ **节点状态监控**：在线节点数量和健康状态
- ✅ **自动刷新**：30秒自动刷新机制
- ✅ **历史记录**：完整的操作日志和进度历史

#### 🤖 智能代理系统
- ✅ **自动注册**：节点自动注册和认证
- ✅ **心跳机制**：实时健康状态上报
- ✅ **任务分发**：智能任务分配和负载均衡
- ✅ **多线程执行**：并发任务处理能力
- ✅ **资源管理**：自动挂载点清理和资源释放

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue3 前端     │    │   Flask 后端    │    │  Proxy Agent    │
│                 │    │                 │    │                 │
│ • 任务管理界面  │◄──►│ • RESTful API   │◄──►│ • 任务执行      │
│ • 实时状态显示  │    │ • JWT 认证      │    │ • 存储操作      │
│ • 统计面板      │    │ • 数据库管理    │    │ • 进度上报      │
│ • 操作日志      │    │ • 任务调度      │    │ • 健康监控      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MySQL 数据库  │
                    │                 │
                    │ • 任务数据      │
                    │ • 节点信息      │
                    │ • 存储配置      │
                    │ • 操作日志      │
                    └─────────────────┘
```

## 快速部署

### 1. 环境要求

**服务端：**
- Python 3.8+
- MySQL 5.7+
- Node.js 16+
- Redis（可选，用于缓存）

**代理端：**
- Python 3.8+
- rclone（用于S3等对象存储）
- NFS/SMB客户端工具

### 2. 后端部署

```bash
# 1. 克隆代码
git clone <repository>
cd easysync/backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库
# 修改 config/default.py 中的数据库配置

# 4. 初始化数据库
python init_db.py

# 5. 启动服务
python run.py
```

### 3. 前端部署

```bash
# 1. 进入前端目录
cd easysync/frontend

# 2. 安装依赖
npm install

# 3. 开发模式启动
npm run dev

# 4. 生产模式构建
npm run build
```

### 4. 代理部署

```bash
# 1. 进入代理目录
cd easysync/backend/app/nodes/agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置代理
# 修改 config.json 文件

# 4. 启动代理
python test_enhanced_agent.py
```

## API 接口文档

### 任务管理 API

| 方法 | 路径 | 功能 | 参数 |
|------|------|------|------|
| GET | `/api/tasks` | 获取任务列表 | page, size, status, type |
| POST | `/api/tasks` | 创建任务 | 任务配置JSON |
| GET | `/api/tasks/{id}` | 获取任务详情 | 任务ID |
| POST | `/api/tasks/{id}/start` | 启动任务 | node_id(可选) |
| POST | `/api/tasks/{id}/pause` | 暂停任务 | - |
| POST | `/api/tasks/{id}/resume` | 恢复任务 | - |
| POST | `/api/tasks/{id}/cancel` | 取消任务 | - |
| POST | `/api/tasks/{id}/retry` | 重试任务 | - |
| DELETE | `/api/tasks/{id}` | 删除任务 | force(可选) |

### 测试 API

| 方法 | 路径 | 功能 | 参数 |
|------|------|------|------|
| POST | `/api/tasks/test-connection` | 连接测试 | storage_config |
| POST | `/api/tasks/test-mount` | 挂载测试 | mount_point, storage_config |

### 统计 API

| 方法 | 路径 | 功能 | 参数 |
|------|------|------|------|
| GET | `/api/tasks/statistics` | 任务统计 | include_all(可选) |

### Agent API

| 方法 | 路径 | 功能 | 参数 |
|------|------|------|------|
| POST | `/api/agent/register` | 节点注册 | 节点信息 |
| POST | `/api/agent/{node_id}/heartbeat` | 发送心跳 | 系统信息 |
| GET | `/api/agent/{node_id}/tasks` | 获取任务 | - |
| PUT | `/api/agent/{node_id}/tasks/{task_id}/status` | 更新状态 | 状态信息 |
| POST | `/api/agent/{node_id}/tasks/{task_id}/logs` | 上报日志 | 日志信息 |

## 配置说明

### 服务端配置 (backend/config/default.py)

```python
# 数据库配置
SQLALCHEMY_DATABASE_URI = 'mysql://user:password@localhost/easysync'

# JWT配置
JWT_SECRET_KEY = 'your-secret-key'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# 文件上传配置
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
```

### 代理配置 (backend/app/nodes/agent/config.json)

```json
{
  "server": {
    "host": "localhost",
    "port": 5000
  },
  "node": {
    "user": 1,
    "id": null,
    "token": null
  },
  "heartbeat_interval": 30,
  "task_poll_interval": 10,
  "task_manager": {
    "max_retries": 3,
    "retry_delay": 5,
    "task_timeout": 3600
  },
  "connection_check": {
    "timeout": 30,
    "retry_count": 3,
    "retry_delay": 2
  }
}
```

## 功能测试

### 运行系统测试

```bash
# 在项目根目录运行
python test_system.py --server http://localhost:5000 --username admin --password admin
```

### 测试覆盖内容

1. **认证系统**：登录和JWT token验证
2. **任务CRUD**：创建、查询、更新、删除任务
3. **任务操作**：启动、暂停、取消、重试任务
4. **连接测试**：存储连接和挂载测试
5. **统计功能**：任务统计和节点状态
6. **Agent API**：节点注册和通信

## 生产环境部署建议

### 1. 安全配置

- 使用HTTPS协议
- 定期更新JWT密钥
- 启用API访问限制
- 配置防火墙规则

### 2. 性能优化

- 使用Redis作为缓存
- 配置数据库连接池
- 启用gzip压缩
- 使用CDN加速前端资源

### 3. 监控和日志

- 配置日志轮转
- 集成监控系统
- 设置告警规则
- 定期备份数据

### 4. 高可用部署

- 多实例负载均衡
- 数据库主从复制
- 自动故障转移
- 容器化部署

## 故障排查

### 常见问题

1. **任务无法启动**
   - 检查节点是否在线
   - 验证存储配置
   - 查看任务日志

2. **连接测试失败**
   - 检查网络连通性
   - 验证存储凭据
   - 查看防火墙设置

3. **代理无法注册**
   - 检查服务端地址
   - 验证网络连接
   - 查看认证配置

### 日志位置

- 服务端日志：`backend/logs/`
- 代理日志：`backend/app/nodes/agent/logs/`
- 前端日志：浏览器控制台

## 联系支持

如果遇到问题，请提供以下信息：
- 系统版本信息
- 错误日志
- 配置文件（脱敏后）
- 重现步骤

---

**EasySync Team**  
版本：1.0.0  
更新时间：2024年12月