# EasySync Proxy Agent API 使用指南

## API 端点总览

Proxy Agent 专用的API端点都在 `/api/agent/` 路径下，与前端Web API（`/api/tasks/`）分离。

### 🔐 认证方式

所有Agent API都需要节点Token认证：
```bash
Authorization: Bearer <node_token>
```

### 📋 API 列表

| 方法 | 端点 | 描述 | 用途 |
|------|------|------|------|
| POST | `/api/agent/{node_id}/register` | 节点注册 | 首次启动时注册 |
| POST | `/api/agent/{node_id}/heartbeat` | 心跳上报 | 定期发送在线状态 |
| GET | `/api/agent/{node_id}/tasks` | 获取任务列表 | 拉取分配的任务 |
| GET | `/api/agent/{node_id}/tasks/{task_id}` | 获取任务详情 | 获取单个任务完整信息 |
| PUT | `/api/agent/{node_id}/tasks/{task_id}/status` | 更新任务状态 | 上报执行状态 |
| POST | `/api/agent/{node_id}/tasks/{task_id}/logs` | 上报任务日志 | 发送进度和日志 |
| POST | `/api/agent/{node_id}/storage/{storage_id}/test` | 测试存储连接 | 获取存储配置并测试 |
| POST | `/api/agent/{node_id}/metrics` | 上报监控数据 | 发送系统指标 |
| POST | `/api/agent/{node_id}/errors` | 上报错误 | 发送错误信息 |
| POST | `/api/agent/{node_id}/alerts` | 发送告警 | 发送告警信息 |

## 📝 API 使用示例

### 1. 节点注册

```python
import requests

def register_node():
    response = requests.post(
        f"{server_url}/api/agent/{node_id}/register",
        json={
            "name": "prod-sync-node-01",
            "ipaddress": "192.168.1.100",
            "version": "1.0.0",
            "user_id": "user-uuid-here",
            "system_info": {
                "os": "ubuntu",
                "version": "20.04",
                "arch": "x86_64",
                "cpu_cores": 8,
                "memory_gb": 16
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data['data']['token']
        return token
```

### 2. 获取任务（包含存储配置）

```python
def fetch_tasks_with_storage_config():
    response = requests.get(
        f"{server_url}/api/agent/{node_id}/tasks",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code == 200:
        tasks = response.json()['data']
        for task in tasks:
            print(f"任务: {task['name']}")
            print(f"源端类型: {task['source_type']}")
            
            # 源端存储配置
            if 'source_storage_config' in task:
                storage = task['source_storage_config']
                print(f"源端存储: {storage['name']} ({storage['type']})")
                print(f"存储配置: {storage['config']}")
            
            # 目标端存储配置
            if 'target_storage_config' in task:
                storage = task['target_storage_config']
                print(f"目标存储: {storage['name']} ({storage['type']})")
                print(f"存储配置: {storage['config']}")
        
        return tasks
```

### 3. 上报任务进度

```python
def report_task_progress(task_id, progress, message, details=None):
    payload = {
        'status': 'progress',
        'message': f"进度 {progress}%: {message}",
        'details': {
            'progress': progress,
            'current_step': message,
            'step_details': details or {}
        }
    }
    
    response = requests.post(
        f"{server_url}/api/agent/{node_id}/tasks/{task_id}/logs",
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    return response.status_code == 200

# 使用示例
report_task_progress(
    task_id="task-123",
    progress=30,
    message="NAS存储挂载完成",
    details={
        "mount_point": "/tmp/easysync_mount_nas_123",
        "storage_type": "nas",
        "mount_time": "2024-01-15 10:30:00"
    }
)
```

### 4. 更新任务状态

```python
def update_task_status(task_id, status, progress=None, error=None):
    payload = {
        'status': status,
        'progress': progress,
        'error': error
    }
    
    response = requests.put(
        f"{server_url}/api/agent/{node_id}/tasks/{task_id}/status",
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    return response.status_code == 200

# 示例：任务开始
update_task_status("task-123", "running", 0)

# 示例：任务完成
update_task_status("task-123", "completed", 100)

# 示例：任务失败
update_task_status("task-123", "failed", 50, "NAS挂载失败: 连接超时")
```

### 5. 测试存储连接

```python
def test_storage_connection(storage_id):
    response = requests.post(
        f"{server_url}/api/agent/{node_id}/storage/{storage_id}/test",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code == 200:
        storage_config = response.json()['data']['storage_config']
        
        # 根据存储类型进行连接测试
        if storage_config['type'] == 'nas':
            return test_nas_connection(storage_config['config'])
        elif storage_config['type'] == 's3':
            return test_s3_connection(storage_config['config'])
        
    return False

def test_nas_connection(config):
    """测试NAS连接"""
    try:
        # 临时挂载测试
        mount_cmd = [
            'mount', '-t', 'cifs',
            f"//{config['host']}{config['share_path']}",
            "/tmp/test_mount",
            '-o', f"username={config['username']},password={config['password']},ro"
        ]
        
        result = subprocess.run(mount_cmd, capture_output=True, timeout=30)
        
        if result.returncode == 0:
            subprocess.run(['umount', '/tmp/test_mount'])
            return True
        
        return False
        
    except Exception:
        return False
```

### 6. 发送心跳

```python
def send_heartbeat():
    import psutil
    
    payload = {
        'system_info': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg()[0],
            'active_tasks': len(get_running_tasks()),
            'timestamp': datetime.now().isoformat()
        }
    }
    
    response = requests.post(
        f"{server_url}/api/agent/{node_id}/heartbeat",
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    return response.status_code == 200
```

## 🔄 完整工作流程示例

```python
class EasySyncAgent:
    def __init__(self, server_url, node_id):
        self.server_url = server_url
        self.node_id = node_id
        self.token = None
        
    def start(self):
        # 1. 注册节点
        self.token = self.register()
        
        # 2. 启动心跳
        self.start_heartbeat()
        
        # 3. 主循环：获取和执行任务
        while True:
            tasks = self.fetch_tasks()
            for task in tasks:
                self.execute_task(task)
            time.sleep(30)
    
    def execute_task(self, task):
        task_id = task['id']
        
        try:
            # 更新为运行状态
            self.update_task_status(task_id, 'running', 0)
            
            # 根据任务类型执行
            if task['source_type'] == 'storage':
                self.execute_storage_task(task)
            elif task['source_type'] == 'client':
                self.execute_client_task(task)
            
            # 完成
            self.update_task_status(task_id, 'completed', 100)
            
        except Exception as e:
            self.update_task_status(task_id, 'failed', error=str(e))
    
    def execute_storage_task(self, task):
        task_id = task['id']
        
        # 获取存储配置
        source_config = task['source_storage_config']
        target_config = task['target_storage_config']
        
        # 报告进度
        self.report_progress(task_id, 10, "准备源端存储")
        
        # 处理源端存储（例如NAS挂载）
        source_path = self.prepare_storage(source_config, task['source_path'])
        self.report_progress(task_id, 30, f"源端存储准备完成: {source_path}")
        
        # 处理目标端存储
        target_path = self.prepare_storage(target_config, task['target_path'])
        self.report_progress(task_id, 50, f"目标存储准备完成: {target_path}")
        
        # 执行同步
        self.report_progress(task_id, 60, "开始数据同步")
        self.sync_data(source_path, target_path, task['options'])
        
        self.report_progress(task_id, 100, "同步完成")
```

## 💡 设计优势

1. **API分离**: Agent API与Web API完全分离，避免混淆
2. **完整配置**: 任务包含完整的存储配置信息，Agent无需额外请求
3. **进度追踪**: 详细的进度上报和日志记录
4. **错误处理**: 完善的错误上报机制
5. **安全认证**: 基于Token的节点认证
6. **实时监控**: 心跳和监控数据上报

这样的设计确保了Proxy Agent能够：
- 自动获取完整的存储配置信息
- 实时上报任务执行进度
- 独立处理各种存储类型的连接和同步
- 与服务端保持良好的通信和监控