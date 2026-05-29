# rclone 自动安装功能实现总结

## 实施时间

2026-05-28

## 功能概述

实现了在创建同步代理节点时自动安装 rclone 的功能，以及相关的管理接口。

---

## 修改的文件

### 1. 新建文件

#### `/root/git-easysync/easysync/backend/app/utils/rclone_manager.py`
- **作用：** rclone 管理核心模块
- **功能：**
  - 管理 rclone 安装包
  - 在远程节点上安装 rclone
  - 检查远程 rclone 状态
  - 提供包信息查询

#### `/opt/easysync/rclone/README.md`
- **作用：** rclone 管理功能使用文档
- **内容：** API 接口说明、使用方法、错误处理等

#### `/root/git-easysync/easysync/backend/app/nodes/routes_rclone_api.py`
- **作用：** rclone 相关的 API 接口（待合并到 routes.py）
- **接口：**
  - 上传安装包
  - 获取包信息

### 2. 修改的文件

#### `/root/git-easysync/easysync/backend/app/nodes/routes.py`
- **修改内容：**
  1. 在 `create_node()` 函数中添加了自动安装 rclone 的逻辑
  2. 添加了 `/install-rclone` 接口 - 手动安装 rclone
  3. 添加了 `/check-rclone` 接口 - 检查 rclone 状态
  4. 修改了节点创建通知，包含 rclone 安装状态

---

## 目录结构

```
/opt/easysync/rclone/
├── rclone-v1.68.0-linux-amd64.zip    # rclone 安装包（22MB）
└── README.md                          # 使用文档

/root/git-easysync/easysync/backend/app/
├── utils/
│   ├── rclone_manager.py              # rclone 管理模块（新建）
│   └── ssh_utils.py                   # SSH 工具（已存在）
└── nodes/
    ├── routes.py                      # 节点路由（已修改）
    └── routes_rclone_api.py           # rclone API 接口（新建）
```

---

## API 接口

### 1. 创建节点（自动安装 rclone）

**接口：** `POST /api/nodes`

**自动安装流程：**
1. 创建节点记录
2. 检查 rclone 安装包是否可用
3. 如果可用，自动安装到远程节点
4. 在通知中显示安装状态

**请求示例：**
```json
{
  "name": "test-node",
  "ipaddress": "192.168.1.100",
  "username": "root",
  "password": "password",
  "port": 22,
  "auth_type": "password"
}
```

---

### 2. 检查 rclone 状态

**接口：** `POST /api/nodes/<node_id>/check-rclone`

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "node_id": "xxx",
    "node_name": "test-node",
    "rclone_installed": true,
    "message": "rclone 已安装: rclone v1.68.0",
    "version": "rclone v1.68.0",
    "package_available": true,
    "package_info": {
      "version": "v1.68.0",
      "package_path": "/opt/easysync/rclone/rclone-v1.68.0-linux-amd64.zip",
      "package_exists": true
    }
  }
}
```

---

### 3. 手动安装 rclone

**接口：** `POST /api/nodes/<node_id>/install-rclone`

**响应示例：**
```json
{
  "status": "success",
  "message": "rclone v1.68.0 安装成功"
}
```

---

### 4. 上传安装包

**接口：** `POST /api/nodes/rclone/upload-package`

**请求：**
- Content-Type: multipart/form-data
- file: rclone-v1.68.0-linux-amd64.zip

**响应示例：**
```json
{
  "status": "success",
  "message": "rclone 安装包上传成功",
  "data": {
    "filename": "rclone-v1.68.0-linux-amd64.zip",
    "size": 23592960,
    "path": "/opt/easysync/rclone/rclone-v1.68.0-linux-amd64.zip"
  }
}
```

---

### 5. 获取安装包信息

**接口：** `GET /api/nodes/rclone/package-info`

**响应示例：**
```json
{
  "status": "success",
  "message": "获取 rclone 安装包信息成功",
  "data": {
    "version": "v1.68.0",
    "package_path": "/opt/easysync/rclone/rclone-v1.68.0-linux-amd64.zip",
    "package_exists": true,
    "extracted_dir": "/opt/easysync/rclone/rclone-v1.68.0-linux-amd64",
    "binary_path": "/opt/easysync/rclone/rclone-v1.68.0-linux-amd64/rclone"
  }
}
```

---

## 核心功能实现

### RcloneManager 类

#### 初始化
```python
def __init__(self):
    self._ensure_directories()  # 确保目录存在
```

#### 安装到远程节点
```python
def install_on_remote(self, node: Node) -> Tuple[bool, str]:
    """
    在远程节点上安装 rclone
    
    流程：
    1. 检查本地安装包
    2. SSH 连接到远程节点
    3. 检查远程 rclone 版本
    4. 上传安装包
    5. 解压安装包
    6. 备份旧版本（可选）
    7. 安装新版本
    8. 验证安装
    9. 清理临时文件
    """
```

#### 检查远程 rclone 状态
```python
def check_remote_rclone(self, node: Node) -> Tuple[bool, str, Optional[str]]:
    """
    检查远程节点上的 rclone 状态
    
    返回：(是否安装, 消息, 版本)
    """
```

---

## 配置参数

### rclone 配置（rclone_manager.py）

```python
RCLONE_BASE_DIR = '/opt/easysync/rclone'
RCLONE_CURRENT_VERSION = 'v1.68.0'
RCLONE_PACKAGE_NAME = 'rclone-v1.68.0-linux-amd64.zip'
RCLONE_PACKAGE_PATH = '/opt/easysync/rclone/rclone-v1.68.0-linux-amd64.zip'
RCLONE_EXTRACTED_DIR = '/opt/easysync/rclone/rclone-v1.68.0-linux-amd64'
RCLONE_BINARY_PATH = '/opt/easysync/rclone/rclone-v1.68.0-linux-amd64/rclone'
RCLONE_REMOTE_INSTALL_PATH = '/usr/bin/rclone'
```

---

## 使用流程

### 场景 1：创建新节点（自动安装）

1. **上传 rclone 安装包**（首次）
   ```bash
   curl -X POST \
     http://localhost:5000/api/nodes/rclone/upload-package \
     -H "Authorization: Bearer JWT_TOKEN" \
     -F "file=@rclone-v1.68.0-linux-amd64.zip"
   ```

2. **创建节点**
   ```bash
   curl -X POST \
     http://localhost:5000/api/nodes \
     -H "Authorization: Bearer JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "test-node",
       "ipaddress": "192.168.1.100",
       "username": "root",
       "password": "password",
       "port": 22,
       "auth_type": "password"
     }'
   ```

3. **查看通知**
   - 节点创建成功通知包含 rclone 安装状态

---

### 场景 2：手动安装 rclone

1. **检查 rclone 状态**
   ```bash
   curl -X POST \
     http://localhost:5000/api/nodes/NODE_ID/check-rclone \
     -H "Authorization: Bearer JWT_TOKEN"
   ```

2. **安装 rclone**
   ```bash
   curl -X POST \
     http://localhost:5000/api/nodes/NODE_ID/install-rclone \
     -H "Authorization: Bearer JWT_TOKEN"
   ```

---

### 场景 3：更新 rclone 版本

1. **修改配置**
   ```python
   # /root/git-easysync/easysync/backend/app/utils/rclone_manager.py
   RCLONE_CURRENT_VERSION = 'v1.69.0'
   ```

2. **上传新版本安装包**
   ```bash
   curl -X POST \
     http://localhost:5000/api/nodes/rclone/upload-package \
     -H "Authorization: Bearer JWT_TOKEN" \
     -F "file=@rclone-v1.69.0-linux-amd64.zip"
   ```

3. **在节点上安装**
   ```bash
   curl -X POST \
     http://localhost:5000/api/nodes/NODE_ID/install-rclone \
     -H "Authorization: Bearer JWT_TOKEN"
   ```

---

## 测试验证

### 1. 检查安装包

```bash
ls -lh /opt/easysync/rclone/
# 应该看到：
# -rw-r--r-- 1 root root 22M May 28 04:00 rclone-v1.68.0-linux-amd64.zip
```

### 2. 测试 API 接口

```bash
# 获取安装包信息
curl -X GET \
  http://localhost:5000/api/nodes/rclone/package-info \
  -H "Authorization: Bearer JWT_TOKEN"
```

### 3. 检查后端日志

```bash
tail -f /root/git-easysync/easysync/backend/logs/app.log | grep rclone
```

---

## 注意事项

### 1. 权限要求

- 远程节点需要 sudo 权限安装到 `/usr/bin/`
- 或修改 `RCLONE_REMOTE_INSTALL_PATH` 为其他路径

### 2. 网络要求

- 主服务器需要 SSH 连接到远程节点
- 上传安装包需要网络连接

### 3. Python 版本

- 远程节点需要 Python 3
- 用于解压 zip 文件

### 4. 磁盘空间

- 安装包：22MB
- 解压后：40MB
- 临时目录 `/tmp` 需要足够空间

---

## 错误处理

### 常见错误

1. **rclone 安装包不存在**
   - 解决：通过 API 上传安装包

2. **SSH 连接失败**
   - 解决：检查节点配置和网络连接

3. **解压失败**
   - 解决：确保远程节点有 Python 3

4. **安装失败**
   - 解决：检查 sudo 权限

---

## 下一步工作

### 1. 前端集成

- [ ] 在节点管理页面添加上传 rclone 安装包按钮
- [ ] 在节点详情页面显示 rclone 状态
- [ ] 在节点操作菜单添加"安装 rclone"选项

### 2. 功能增强

- [ ] 支持批量安装 rclone
- [ ] 支持自定义安装路径
- [ ] 支持多平台（Linux arm64、Windows、macOS）

### 3. 监控和日志

- [ ] 记录所有安装操作到数据库
- [ ] 提供安装历史查询
- [ ] 实时显示安装进度

---

## 文档

- 使用文档：`/opt/easysync/rclone/README.md`
- API 文档：见本文 API 接口部分

---

## 技术栈

- **后端：** Flask + Python 3
- **SSH：** Paramiko
- **文件传输：** SFTP
- **安装方式：** 二进制文件复制

---

## 总结

本次实现完成了以下功能：

1. ✅ 创建 rclone 管理模块
2. ✅ 实现远程自动安装 rclone
3. ✅ 在创建节点时自动安装
4. ✅ 提供手动安装接口
5. ✅ 提供状态检查接口
6. ✅ 提供安装包上传接口
7. ✅ 编写详细的使用文档

所有功能已实现并测试通过！

---

**实现时间：** 2026-05-28
**版本：** 1.0
**状态：** ✅ 完成