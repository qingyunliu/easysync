# EasySync 部署指南

## 🚀 系统概述

EasySync 是一个企业级文件同步系统，支持多种存储类型之间的数据同步，包括NFS、NAS、OBS对象存储等。系统采用分布式架构，由服务端、代理节点和客户端组成。

## 📋 系统要求

### 服务端要求
- **操作系统**: Ubuntu 18.04+ / CentOS 7+ / RHEL 7+
- **Python**: 3.8+
- **Node.js**: 16+
- **数据库**: MySQL 8.0+ / PostgreSQL 12+
- **Redis**: 6.0+
- **内存**: 最低 4GB，推荐 8GB+
- **存储**: 最低 50GB，推荐 100GB+

### 客户端/代理节点要求
- **操作系统**: Ubuntu 18.04+ / CentOS 7+ / RHEL 7+ / Windows 10+
- **Python**: 3.8+
- **内存**: 最低 2GB，推荐 4GB+
- **存储**: 最低 10GB，推荐 20GB+

## 🏗️ 架构组件

### 核心组件
- **Web服务器**: Flask + Gunicorn
- **前端界面**: Vue 3 + Element Plus
- **任务调度**: APScheduler + Celery
- **消息队列**: Redis
- **数据库**: MySQL/PostgreSQL
- **监控**: Prometheus + Grafana

### 代理组件
- **代理服务**: Python Agent
- **存储连接**: rclone + rsync
- **监控上报**: 系统资源监控
- **任务执行**: 多线程任务处理

## 📦 快速部署

### 1. 环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y python3 python3-pip python3-venv nodejs npm mysql-server redis-server

# 安装系统工具
sudo apt install -y rsync rclone nfs-common cifs-utils

# 创建应用目录
sudo mkdir -p /opt/easysync
sudo chown -R $USER:$USER /opt/easysync
```

### 2. 数据库配置

```bash
# 启动MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 创建数据库
mysql -u root -p << EOF
CREATE DATABASE easysync CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'easysync'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON easysync.* TO 'easysync'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 3. Redis配置

```bash
# 启动Redis
sudo systemctl start redis
sudo systemctl enable redis

# 配置Redis
sudo nano /etc/redis/redis.conf
# 设置: maxmemory 2gb
# 设置: maxmemory-policy allkeys-lru
sudo systemctl restart redis
```

### 4. 后端部署

```bash
# 克隆代码
git clone https://github.com/your-repo/easysync.git
cd easysync

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env
```

#### 环境变量配置 (.env)
```env
# 数据库配置
DATABASE_URL=mysql://easysync:your_password_here@localhost/easysync

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 应用配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# 文件存储
UPLOAD_FOLDER=/opt/easysync/uploads
LOG_FOLDER=/opt/easysync/logs

# 监控配置
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

```bash
# 数据库迁移
flask db upgrade

# 创建管理员用户
python scripts/create_admin.py

# 启动服务
gunicorn -c gunicorn.conf.py app:app
```

### 5. 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 配置Nginx
sudo nano /etc/nginx/sites-available/easysync
```

#### Nginx配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /opt/easysync/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket支持
    location /socket.io {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/easysync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 系统服务配置

#### 创建systemd服务文件

```bash
# 后端服务
sudo nano /etc/systemd/system/easysync-backend.service
```

```ini
[Unit]
Description=EasySync Backend Service
After=network.target mysql.service redis.service

[Service]
Type=exec
User=easysync
Group=easysync
WorkingDirectory=/opt/easysync
Environment=PATH=/opt/easysync/venv/bin
ExecStart=/opt/easysync/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 任务调度服务
sudo nano /etc/systemd/system/easysync-scheduler.service
```

```ini
[Unit]
Description=EasySync Task Scheduler
After=network.target mysql.service redis.service

[Service]
Type=exec
User=easysync
Group=easysync
WorkingDirectory=/opt/easysync
Environment=PATH=/opt/easysync/venv/bin
ExecStart=/opt/easysync/venv/bin/python -m backend.app.tasks.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable easysync-backend easysync-scheduler
sudo systemctl start easysync-backend easysync-scheduler
```

## 🔧 代理节点部署

### 1. 自动安装脚本

```bash
# 在服务端生成安装命令
curl -X POST "http://your-server.com/api/nodes/install-command" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "node_name": "agent-node-01",
    "user_id": "your-user-id"
  }'
```

### 2. 手动安装

```bash
# 创建目录
sudo mkdir -p /opt/easysync/agent
cd /opt/easysync/agent

# 下载代理程序
wget http://your-server.com/api/nodes/agent/download/agent.tar.gz
tar -xzf agent.tar.gz

# 安装依赖
pip3 install -r requirements.txt

# 配置代理
cp config/config.json.example config/config.json
nano config/config.json
```

#### 代理配置文件
```json
{
  "server": {
    "host": "your-server.com",
    "port": 5000,
    "protocol": "http"
  },
  "node": {
    "id": "generated-node-id",
    "name": "agent-node-01",
    "user": "your-user-id",
    "token": "generated-token"
  },
  "heartbeat_interval": 30,
  "task_poll_interval": 10,
  "monitor": {
    "enabled": true,
    "interval": 60,
    "metrics": ["cpu", "memory", "disk", "network"]
  },
  "sync": {
    "max_retries": 3,
    "retry_delay": 5,
    "max_concurrent": 2
  },
  "storage": {
    "temp_dir": "/tmp/easysync",
    "log_dir": "/var/log/easysync"
  }
}
```

```bash
# 安装系统服务
sudo ./install.sh

# 启动代理服务
sudo systemctl start easysync-agent
sudo systemctl enable easysync-agent
```

## 🔒 SSL/TLS配置

### 使用Let's Encrypt

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 2 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控配置

### 1. Prometheus配置

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'easysync-backend'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: /metrics
    
  - job_name: 'easysync-agents'
    static_configs:
      - targets: ['agent1:9090', 'agent2:9090']
```

### 2. Grafana仪表板

```bash
# 导入预配置仪表板
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/easysync-dashboard.json
```

## 🚀 性能优化

### 1. 数据库优化

```sql
-- MySQL优化配置
SET GLOBAL innodb_buffer_pool_size = 2147483648;
SET GLOBAL innodb_log_file_size = 268435456;
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL sync_binlog = 0;
```

### 2. Redis优化

```bash
# 内存优化
echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf
echo never > /sys/kernel/mm/transparent_hugepage/enabled
```

### 3. 应用优化

```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
```

## 🔧 维护操作

### 1. 备份策略

```bash
#!/bin/bash
# backup.sh

# 数据库备份
mysqldump -u easysync -p easysync > /backup/easysync_$(date +%Y%m%d).sql

# 文件备份
tar -czf /backup/easysync_files_$(date +%Y%m%d).tar.gz /opt/easysync/uploads

# 配置备份
cp /opt/easysync/.env /backup/env_$(date +%Y%m%d)
```

### 2. 日志管理

```bash
# 配置logrotate
sudo nano /etc/logrotate.d/easysync
```

```
/opt/easysync/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        systemctl reload easysync-backend
    endscript
}
```

### 3. 健康检查

```bash
#!/bin/bash
# health_check.sh

# 检查服务状态
systemctl is-active easysync-backend
systemctl is-active easysync-scheduler

# 检查端口
netstat -tlnp | grep :5000

# 检查数据库连接
mysql -u easysync -p -e "SELECT 1"

# 检查Redis连接
redis-cli ping
```

## 🐛 故障排除

### 常见问题

1. **服务无法启动**
   - 检查日志: `journalctl -u easysync-backend -f`
   - 检查配置: 验证环境变量和数据库连接

2. **代理连接失败**
   - 检查网络连接
   - 验证token有效性
   - 检查防火墙设置

3. **任务执行失败**
   - 检查存储连接
   - 验证权限设置
   - 查看任务日志

### 日志位置

- **后端日志**: `/opt/easysync/logs/backend.log`
- **任务日志**: `/opt/easysync/logs/tasks.log`
- **代理日志**: `/opt/easysync/agent/logs/agent.log`
- **Nginx日志**: `/var/log/nginx/access.log`

## 📞 技术支持

如需技术支持，请提供以下信息：
- 系统版本和配置
- 错误日志
- 重现步骤
- 环境信息

---

*此部署指南涵盖了EasySync系统的完整部署流程，如有问题请参考故障排除章节或联系技术支持。*