# EasySync Agent

EasySync Agent是一个用于数据同步的代理程序，可以安装在客户端，用于与服务端进行通信和数据同步。

## 功能特点

- 自动注册到服务端
- 定期上报心跳
- 定期上报监控数据
- 接收并执行服务端任务
- 支持多种存储类型（NFS、Samba、Local、OBS）
- 支持数据同步
- 支持资源监控
- 支持告警功能

## 系统架构

### 目录结构
```
agent/
├── config/             # 配置文件
│   ├── config.json    # 默认配置
│   └── settings.py    # 配置管理
├── core/              # 核心功能
│   ├── agent.py       # 代理核心
│   ├── communication.py # 通信管理
│   ├── storage.py     # 存储管理
│   └── progress.py    # 进度监控
├── models/            # 数据模型
│   └── task_state.py  # 任务状态
├── services/          # 服务
│   ├── monitor_service.py # 监控服务
│   └── sync_service.py    # 同步服务
├── utils/             # 工具函数
│   ├── logger.py      # 日志管理
│   └── resource.py    # 资源管理
├── main.py            # 主程序
├── requirements.txt   # 依赖
└── README.md          # 说明文档
```

### 核心模块

#### 1. ProxyAgent
代理核心类，负责：
- 节点注册
- 心跳上报
- 任务接收
- 服务管理

主要接口：
```python
class ProxyAgent:
    def __init__(self, config: Dict[str, Any])
    def start()  # 启动代理
    def stop()   # 停止代理
    def wait()   # 等待运行
    def is_healthy() -> bool  # 健康检查
```

#### 2. StorageManager
存储管理类，负责：
- 存储挂载/卸载
- 存储检查
- 数据同步
- 进度监控

主要接口：
```python
class StorageManager:
    def mount_storage(config: Dict[str, Any]) -> Optional[str]
    def unmount_storage(mount_point: str) -> bool
    def check_storage(config: Dict[str, Any]) -> bool
    def sync_data(source_config: Dict[str, Any], target_config: Dict[str, Any], 
                 options: Dict[str, Any] = None, progress_callback: Optional[Callable] = None) -> bool
```

#### 3. SyncService
同步服务类，负责：
- 任务队列管理
- 任务执行
- 状态更新
- 进度回调

主要接口：
```python
class SyncService:
    def add_task(task: Dict[str, Any])
    def get_task_status(task_id: str) -> Optional[Dict[str, Any]]
    def cleanup_old_tasks(max_age_days: int = 7)
```

#### 4. MonitorService
监控服务类，负责：
- 系统资源监控
- 告警管理
- 指标收集
- 数据上报

主要接口：
```python
class MonitorService:
    def get_metrics() -> Dict[str, Any]
    def add_callback(callback: Callable[[Dict[str, Any]], None])
    def remove_callback(callback: Callable[[Dict[str, Any]], None])
```

#### 5. ServerCommunication
服务器通信类，负责：
- 与服务器建立连接
- 发送心跳
- 接收任务
- 上报状态
- 错误处理

主要接口：
```python
class ServerCommunication:
    def __init__(self, config: Dict[str, Any])
    def connect() -> bool  # 连接服务器
    def disconnect()  # 断开连接
    def send_heartbeat(node_info: Dict[str, Any]) -> bool  # 发送心跳
    def get_tasks() -> List[Dict[str, Any]]  # 获取任务
    def update_task_status(task_id: str, status: Dict[str, Any]) -> bool  # 更新任务状态
    def report_metrics(metrics: Dict[str, Any]) -> bool  # 上报监控指标
    def report_error(error: Dict[str, Any]) -> bool  # 上报错误
```

通信接口参数说明：

1. 心跳接口
```python
# 发送心跳
def send_heartbeat(node_info: Dict[str, Any]) -> bool
API路径：POST /api/v1/nodes/{node_id}/heartbeat
参数：
    node_info: {
        "node_id": str,  # 节点ID
        "hostname": str,  # 主机名
        "ip": str,  # IP地址
        "status": str,  # 节点状态
        "version": str,  # 版本号
        "last_heartbeat": int,  # 上次心跳时间
        "metrics": {  # 系统指标
            "cpu_percent": float,
            "memory_percent": float,
            "disk_percent": float,
            "network_io": Dict[str, int]
        }
    }
返回：
    bool: 是否成功
```

2. 任务接口
```python
# 获取任务
def get_tasks() -> List[Dict[str, Any]]
API路径：GET /api/v1/nodes/{node_id}/tasks
返回：
    List[Dict[str, Any]]: 任务列表，每个任务包含：
    {
        "task_id": str,  # 任务ID
        "type": str,  # 任务类型
        "source": {  # 源存储配置
            "type": str,  # 存储类型
            "config": Dict[str, Any]  # 存储配置
        },
        "target": {  # 目标存储配置
            "type": str,
            "config": Dict[str, Any]
        },
        "options": {  # 任务选项
            "max_retries": int,
            "retry_delay": int,
            "timeout": int
        }
    }

# 更新任务状态
def update_task_status(task_id: str, status: Dict[str, Any]) -> bool
API路径：PUT /api/v1/nodes/{node_id}/tasks/{task_id}/status
参数：
    task_id: str  # 任务ID
    status: {
        "state": str,  # 任务状态
        "progress": float,  # 进度
        "error": Optional[str],  # 错误信息
        "start_time": int,  # 开始时间
        "end_time": Optional[int],  # 结束时间
        "details": Dict[str, Any]  # 详细信息
    }
返回：
    bool: 是否成功
```

3. 监控接口
```python
# 上报监控指标
def report_metrics(metrics: Dict[str, Any]) -> bool
API路径：POST /api/v1/nodes/{node_id}/metrics
参数：
    metrics: {
        "node_id": str,  # 节点ID
        "timestamp": int,  # 时间戳
        "cpu": {  # CPU指标
            "percent": float,
            "load": List[float]
        },
        "memory": {  # 内存指标
            "total": int,
            "available": int,
            "percent": float
        },
        "disk": {  # 磁盘指标
            "total": int,
            "used": int,
            "free": int,
            "percent": float
        },
        "network": {  # 网络指标
            "bytes_sent": int,
            "bytes_recv": int,
            "packets_sent": int,
            "packets_recv": int
        }
    }
返回：
    bool: 是否成功
```

4. 错误接口
```python
# 上报错误
def report_error(error: Dict[str, Any]) -> bool
API路径：POST /api/v1/nodes/{node_id}/errors
参数：
    error: {
        "node_id": str,  # 节点ID
        "timestamp": int,  # 时间戳
        "level": str,  # 错误级别
        "type": str,  # 错误类型
        "message": str,  # 错误信息
        "details": Dict[str, Any],  # 详细信息
        "stack_trace": Optional[str]  # 堆栈跟踪
    }
返回：
    bool: 是否成功
```

5. 节点注册接口
```python
# 注册节点
def register_node(node_info: Dict[str, Any]) -> Optional[str]
API路径：POST /api/v1/nodes
参数：
    node_info: {
        "hostname": str,  # 主机名
        "ip": str,  # IP地址
        "version": str,  # 版本号
        "capabilities": List[str],  # 支持的功能
        "config": Dict[str, Any]  # 节点配置
    }
返回：
    Optional[str]: 节点ID，注册失败返回None
```

6. 节点注销接口
```python
# 注销节点
def unregister_node(node_id: str) -> bool
API路径：DELETE /api/v1/nodes/{node_id}
参数：
    node_id: str  # 节点ID
返回：
    bool: 是否成功
```

7. 节点配置更新接口
```python
# 更新节点配置
def update_node_config(node_id: str, config: Dict[str, Any]) -> bool
API路径：PUT /api/v1/nodes/{node_id}/config
参数：
    node_id: str  # 节点ID
    config: Dict[str, Any]  # 新的配置
返回：
    bool: 是否成功
```

8. 节点状态查询接口
```python
# 查询节点状态
def get_node_status(node_id: str) -> Optional[Dict[str, Any]]
API路径：GET /api/v1/nodes/{node_id}/status
参数：
    node_id: str  # 节点ID
返回：
    Optional[Dict[str, Any]]: 节点状态信息，查询失败返回None
```

### API接口说明

1. 接口版本
- 所有接口都使用`/api/v1`作为基础路径
- 版本号在URL中体现，便于后续升级

2. 认证方式
- 所有接口都需要在请求头中包含`Authorization: Bearer {token}`
- token通过节点注册时获取

3. 错误处理
- 所有接口在发生错误时返回对应的HTTP状态码
- 错误响应格式：
```json
{
    "error": {
        "code": int,  # 错误码
        "message": str,  # 错误信息
        "details": Dict[str, Any]  # 详细信息
    }
}
```

4. 通用状态码
- 200: 成功
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

5. 请求限制
- 心跳接口：每30秒一次
- 监控接口：每5秒一次
- 任务状态更新：每10秒一次
- 错误上报：实时

### 通信流程

1. 连接流程
```
ServerCommunication
  ├── 初始化配置
  ├── 建立连接
  │   ├── 验证服务器地址
  │   ├── 建立HTTP连接
  │   └── 验证API版本
  └── 注册节点
      ├── 发送注册请求
      └── 获取节点ID
```

2. 心跳流程
```
ServerCommunication
  └── send_heartbeat
      ├── 收集节点信息
      ├── 收集系统指标
      ├── 发送心跳请求
      └── 处理响应
          ├── 成功：更新状态
          └── 失败：重试或报告错误
```

3. 任务流程
```
ServerCommunication
  ├── get_tasks
  │   ├── 发送任务请求
  │   └── 处理响应
  │       ├── 成功：返回任务列表
  │       └── 失败：重试或报告错误
  └── update_task_status
      ├── 准备状态信息
      ├── 发送状态更新
      └── 处理响应
          ├── 成功：更新本地状态
          └── 失败：重试或报告错误
```

4. 监控流程
```
ServerCommunication
  └── report_metrics
      ├── 收集系统指标
      ├── 发送指标数据
      └── 处理响应
          ├── 成功：更新本地记录
          └── 失败：重试或报告错误
```

5. 错误处理流程
```
ServerCommunication
  └── report_error
      ├── 收集错误信息
      ├── 发送错误报告
      └── 处理响应
          ├── 成功：更新错误状态
          └── 失败：记录到本地日志
```

## 配置说明

### 1. 基本配置
```json
{
    "server": {
        "host": "localhost",
        "port": 5000,
        "api_version": "v1"
    },
    "heartbeat_interval": 30,
    "health_check_interval": 60
}
```

### 2. 监控配置
```json
{
    "monitor": {
        "interval": 5,
        "max_history": 1000,
        "alert_thresholds": {
            "cpu_percent": 90,
            "memory_percent": 90,
            "disk_percent": 90
        }
    }
}
```

### 3. 同步配置
```json
{
    "sync": {
        "max_retries": 3,
        "retry_delay": 5,
        "max_concurrent": 1
    }
}
```

### 4. 存储配置
```json
{
    "storage": {
        "mount_base": "/mnt/easysync",
        "nfs": {
            "server": "nfs.server.com",
            "path": "/data",
            "options": "vers=4"
        },
        "samba": {
            "server": "samba.server.com",
            "share": "data",
            "username": "user",
            "password": "pass"
        },
        "obs": {
            "provider": "AWS",
            "access_key": "YOUR_ACCESS_KEY",
            "secret_key": "YOUR_SECRET_KEY",
            "region": "us-west-2",
            "endpoint": "s3.amazonaws.com",
            "bucket": "your-bucket"
        }
    }
}
```

## 技术逻辑流程

### 1. 启动流程
```
main.py
  ├── 解析命令行参数
  ├── 设置日志系统
  ├── 加载配置
  ├── 注册信号处理
  └── 创建并启动ProxyAgent
      ├── 注册节点
      ├── 启动监控服务
      ├── 启动同步服务
      ├── 启动心跳线程
      └── 启动健康检查线程
```

### 2. 心跳流程
```
ProxyAgent
  └── _heartbeat_loop
      ├── 获取系统信息
      ├── 发送心跳
      └── 获取任务
          └── 添加到SyncService
```

### 3. 同步流程
```
SyncService
  ├── add_task
  │   ├── 检查任务ID
  │   ├── 检查任务状态
  │   └── 添加到队列
  └── _sync_loop
      ├── 检查资源
      ├── 检查并发
      ├── 获取任务
      └── 执行任务
          ├── 初始化状态
          ├── 检查存储
          └── 执行同步
              ├── 挂载存储
              ├── 执行同步
              └── 卸载存储
```

### 4. 存储管理流程
```
StorageManager
  ├── 挂载存储
  │   ├── 检查存储类型
  │   ├── 创建挂载点
  │   └── 执行挂载
  ├── 卸载存储
  │   ├── 执行卸载
  │   ├── 删除挂载点
  │   └── 清理记录
  ├── 存储检查
  │   ├── 检查类型
  │   ├── 尝试挂载
  │   └── 验证可用性
  └── 同步数据
      ├── 根据类型选择方式
      ├── 执行同步
      └── 更新进度
```

## 使用说明

### 1. 安装
```bash
# 克隆代码库
git clone https://github.com/yourusername/easysync.git
cd easysync/backend/app/nodes/agent

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置
1. 复制默认配置文件：
```bash
cp config/config.json.example config/config.json
```

2. 修改配置文件：
- 设置服务器信息
- 配置存储信息
- 调整监控参数
- 设置同步选项

### 3. 运行
```bash
# 使用默认配置
python main.py

# 指定配置文件
python main.py --config /path/to/config.json

# 指定日志级别
python main.py --log-level DEBUG
```

### 4. 监控
- 查看日志：`logs/agent.log`
- 查看状态：`state/`目录
- 查看挂载点：`/mnt/easysync/`

### 5. 常见问题
1. 存储挂载失败
   - 检查存储配置
   - 检查网络连接
   - 检查权限设置

2. 同步失败
   - 检查存储可用性
   - 检查资源限制
   - 查看错误日志

3. 心跳失败
   - 检查网络连接
   - 检查服务器状态
   - 检查配置信息

## 开发指南

### 1. 添加新的存储类型
1. 在`StorageManager`中添加新的挂载方法
2. 实现存储检查逻辑
3. 添加同步支持
4. 更新配置验证

### 2. 添加新的监控指标
1. 在`MonitorService`中添加新的指标收集
2. 更新告警阈值
3. 添加指标处理
4. 更新配置验证

### 3. 添加新的同步方式
1. 在`StorageManager`中添加新的同步方法
2. 实现进度监控
3. 添加错误处理
4. 更新配置验证

## 许可证

MIT 