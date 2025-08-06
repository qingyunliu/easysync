# Proxy节点任务执行指南

## 任务配置获取

当proxy节点获取任务时，API会返回完整的存储配置信息：

```json
{
  "status": "success",
  "data": [
    {
      "id": "task-123",
      "name": "NAS到S3同步任务",
      "type": "sync",
      "source_type": "storage",
      "source_path": "/data/backup",
      "target_path": "backup-bucket/data",
      "source_storage_config": {
        "id": "storage-456",
        "name": "生产环境NAS",
        "type": "nas",
        "config": {
          "host": "192.168.1.100",
          "share_path": "/volume1/data",
          "username": "syncuser",
          "password": "encrypted_password",
          "protocol": "smb",
          "port": 445
        }
      },
      "target_storage_config": {
        "id": "storage-789",
        "name": "AWS S3存储",
        "type": "s3",
        "config": {
          "access_key": "AKIAXXXXX",
          "secret_key": "encrypted_secret",
          "bucket": "backup-bucket",
          "region": "us-east-1",
          "endpoint": ""
        }
      },
      "options": {
        "delete": false,
        "compress": true,
        "checksum": true,
        "bandwidth_limit": 100,
        "max_connections": 2
      }
    }
  ]
}
```

## 不同存储类型的处理

### 1. NAS存储处理

```python
def handle_nas_storage(storage_config, task_path):
    """处理NAS存储挂载"""
    config = storage_config['config']
    
    # 生成随机挂载点，避免冲突
    mount_point = f"/tmp/easysync_mount_{storage_config['id']}_{int(time.time())}"
    
    # 创建挂载点
    os.makedirs(mount_point, exist_ok=True)
    
    try:
        # 根据协议选择挂载方式
        if config['protocol'] == 'smb':
            mount_cmd = [
                'mount', '-t', 'cifs',
                f"//{config['host']}{config['share_path']}",
                mount_point,
                '-o', f"username={config['username']},password={config['password']},port={config['port']}"
            ]
        elif config['protocol'] == 'nfs':
            mount_cmd = [
                'mount', '-t', 'nfs',
                f"{config['host']}:{config['share_path']}",
                mount_point
            ]
        
        # 执行挂载
        result = subprocess.run(mount_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"挂载失败: {result.stderr}")
        
        # 返回本地路径
        return os.path.join(mount_point, task_path.lstrip('/'))
        
    except Exception as e:
        # 清理挂载点
        if os.path.exists(mount_point):
            os.rmdir(mount_point)
        raise e
```

### 2. S3存储处理

```python
def handle_s3_storage(storage_config, task_path):
    """处理S3存储配置"""
    config = storage_config['config']
    
    # 生成rclone配置
    rclone_config = {
        'type': 's3',
        'access_key_id': config['access_key'],
        'secret_access_key': config['secret_key'],
        'region': config['region'],
        'endpoint': config.get('endpoint', ''),
        'location_constraint': config['region']
    }
    
    # 返回rclone路径格式
    remote_name = f"s3_{storage_config['id']}"
    return f"{remote_name}:{task_path}", rclone_config
```

### 3. 本地存储处理

```python
def handle_local_storage(storage_config, task_path):
    """处理本地存储"""
    config = storage_config['config']
    base_path = config.get('base_path', '/data')
    
    # 组合完整路径
    full_path = os.path.join(base_path, task_path.lstrip('/'))
    
    # 检查路径是否存在
    if not os.path.exists(os.path.dirname(full_path)):
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    return full_path
```

## 任务执行流程

### 1. 存储模式任务执行

```python
def execute_storage_task(task):
    """执行存储到存储的同步任务"""
    source_config = task['source_storage_config']
    target_config = task['target_storage_config']
    
    source_path = None
    target_path = None
    mount_points = []
    
    try:
        # 处理源端存储
        if source_config['type'] in ['nas', 'nfs']:
            source_path = handle_nas_storage(source_config, task['source_path'])
            mount_points.append(source_path)
        elif source_config['type'] in ['s3', 'obs']:
            source_path, source_rclone_config = handle_s3_storage(source_config, task['source_path'])
        else:
            source_path = handle_local_storage(source_config, task['source_path'])
        
        # 处理目标端存储
        if target_config['type'] in ['nas', 'nfs']:
            target_path = handle_nas_storage(target_config, task['target_path'])
            mount_points.append(target_path)
        elif target_config['type'] in ['s3', 'obs']:
            target_path, target_rclone_config = handle_s3_storage(target_config, task['target_path'])
        else:
            target_path = handle_local_storage(target_config, task['target_path'])
        
        # 执行同步
        sync_result = execute_sync(source_path, target_path, task['options'])
        
        return sync_result
        
    finally:
        # 清理挂载点
        cleanup_mounts(mount_points)
```

### 2. 客户端模式任务执行

```python
def execute_client_task(task):
    """执行客户端任务（由客户端本地agent处理）"""
    client_config = task['source_client_config']
    target_config = task['target_storage_config']
    
    # 构建任务配置发送给客户端
    client_task = {
        'id': task['id'],
        'source_path': task['source_path'],
        'target_storage_config': target_config,
        'target_path': task['target_path'],
        'options': task['options']
    }
    
    # 通过WebSocket或HTTP发送任务给客户端
    send_task_to_client(client_config['ip_address'], client_task)
```

## 连接测试

```python
def test_storage_connection(storage_config):
    """测试存储连接"""
    if storage_config['type'] == 'nas':
        return test_nas_connection(storage_config)
    elif storage_config['type'] == 's3':
        return test_s3_connection(storage_config)
    elif storage_config['type'] == 'local':
        return test_local_connection(storage_config)
    else:
        return False, f"不支持的存储类型: {storage_config['type']}"

def test_nas_connection(storage_config):
    """测试NAS连接"""
    config = storage_config['config']
    try:
        # 尝试临时挂载测试
        test_mount_point = f"/tmp/test_mount_{int(time.time())}"
        os.makedirs(test_mount_point, exist_ok=True)
        
        # 执行挂载测试
        mount_cmd = [
            'mount', '-t', 'cifs',
            f"//{config['host']}{config['share_path']}",
            test_mount_point,
            '-o', f"username={config['username']},password={config['password']},ro"
        ]
        
        result = subprocess.run(mount_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # 卸载测试挂载
            subprocess.run(['umount', test_mount_point], capture_output=True)
            os.rmdir(test_mount_point)
            return True, "NAS连接测试成功"
        else:
            return False, f"NAS连接失败: {result.stderr}"
            
    except Exception as e:
        return False, f"NAS连接测试异常: {str(e)}"
```

## 进度上报

```python
def report_task_progress(task_id, progress, message, details=None):
    """上报任务进度"""
    payload = {
        'task_id': task_id,
        'progress': progress,
        'current_step': message,
        'total_steps': 100,
        'step_details': details or {}
    }
    
    response = requests.post(
        f"{SERVER_URL}/api/tasks/{task_id}/logs/progress",
        json=payload,
        headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
    )
    
    return response.status_code == 200
```

这种设计的优势：

1. **配置集中管理**：存储配置在服务端统一管理，proxy获取时自动包含
2. **安全性**：敏感信息（密码、密钥）在传输时可以加密
3. **灵活性**：支持多种存储类型的混合同步
4. **可追溯性**：所有配置变更都有记录
5. **易维护**：配置更新后无需重新部署proxy

您觉得这个方案如何？有需要调整的地方吗？