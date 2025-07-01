# EasySync Agent

EasySync Agent 是一个轻量级的系统监控和文件同步代理程序，用于与服务端进行通信，执行监控数据采集和文件同步任务。

## 功能特性

- 系统监控（CPU、内存、磁盘、网络）
- 文件同步（基于rsync）
- WebSocket实时通信
- 配置热重载
- 健康检查
- 日志轮转

## 系统要求

- Go 1.16 或更高版本
- Linux/Unix 系统（支持 macOS）
- 足够的磁盘空间用于日志存储

## 安装部署

### 1. 编译

```bash
# 克隆仓库
git clone https://github.com/yourusername/easysync.git
cd easysync/backend/app/clients/agent

# 编译
go build -o easysync-agent
```

### 2. 配置

创建配置文件 `config.yaml`：

```yaml
# 服务端配置
server:
  url: "ws://your-server:8080/ws"  # WebSocket服务器地址
  heartbeat_interval: 30s          # 心跳间隔

# 监控配置
monitor:
  interval: 5s                     # 监控数据采集间隔
  cpu_enabled: true               # 是否启用CPU监控
  memory_enabled: true            # 是否启用内存监控
  network_enabled: true           # 是否启用网络监控
  disk_enabled: true              # 是否启用磁盘监控

# 同步配置
sync:
  max_retries: 3                  # 最大重试次数
  retry_interval: 1s              # 重试间隔
  default_timeout: 30m            # 默认超时时间

# 日志配置
log:
  level: "info"                   # 日志级别
  max_size: 100                   # 单个日志文件最大大小(MB)
  max_backups: 3                  # 最大备份数
  max_age: 7                      # 日志保留天数
```

### 3. 运行

```bash
# 直接运行
./easysync-agent -config config.yaml

# 作为系统服务运行（Linux）
sudo cp easysync-agent /usr/local/bin/
sudo cp easysync-agent.service /etc/systemd/system/
sudo systemctl enable easysync-agent
sudo systemctl start easysync-agent
```

## 使用说明

### 1. 与服务端连接

Agent启动后会自动连接到配置的服务端WebSocket地址。连接成功后：

- 每30秒发送一次心跳包
- 每5秒上报一次监控数据
- 等待接收同步任务

### 2. 监控数据

Agent会定期采集以下监控数据：

- CPU使用率
- 内存使用情况
- 磁盘使用情况
- 网络流量统计

监控数据格式示例：
```json
{
    "timestamp": "2024-03-20T10:00:00Z",
    "cpu": 45.5,
    "memory": {
        "total": 8589934592,
        "used": 4294967296,
        "used_percent": 50.0
    },
    "network": {
        "receive": 1024000,
        "send": 512000
    },
    "disk": {
        "total": 107374182400,
        "used": 53687091200,
        "used_percent": 50.0
    }
}
```

### 3. 同步任务

Agent接收的同步任务格式：
```json
{
    "id": "task-123",
    "source": "/path/to/source",
    "destination": "user@remote:/path/to/destination",
    "options": {
        "exclude_patterns": ["*.tmp", "*.log"],
        "include_patterns": ["*.txt"],
        "delete": true,
        "compress": true,
        "bandwidth_limit": 1000,
        "timeout": 30
    },
    "schedule": {
        "type": "interval",
        "interval": 300
    }
}
```

### 4. 健康检查

Agent会定期向服务端发送健康状态：
```json
{
    "status": "ok",
    "components": {
        "websocket": true,
        "monitor": true,
        "syncer": true
    },
    "uptime": "1h30m",
    "version": "1.0.0"
}
```

## 故障排除

### 1. 连接问题

如果Agent无法连接到服务端：
- 检查网络连接
- 确认服务端地址和端口是否正确
- 检查防火墙设置
- 查看日志文件中的错误信息

### 2. 监控数据异常

如果监控数据异常：
- 检查系统权限
- 确认监控间隔是否合理
- 查看系统资源使用情况

### 3. 同步任务失败

如果同步任务失败：
- 检查源目录和目标目录权限
- 确认rsync是否安装
- 检查网络连接
- 查看任务日志

## 日志管理

日志文件位置：`/var/log/easysync/agent.log`

日志轮转配置：
- 单个文件最大100MB
- 保留最近3个备份
- 日志保留7天

## 信号处理

Agent支持以下信号：
- SIGINT/SIGTERM: 优雅关闭
- SIGHUP: 重载配置

## 安全建议

1. 使用最小权限原则运行Agent
2. 定期更新到最新版本
3. 使用安全的WebSocket连接（wss://）
4. 限制同步目录的访问权限
5. 定期检查日志文件

## 常见问题

1. Q: Agent无法启动
   A: 检查配置文件格式和权限

2. Q: 监控数据不更新
   A: 检查监控间隔设置和系统权限

3. Q: 同步任务失败
   A: 检查rsync配置和网络连接

## 联系方式

如有问题，请联系：your-email@example.com
