FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    rsync \
    nfs-common \
    cifs-utils \
    curl \
    wget \
    psmisc \
    && rm -rf /var/lib/apt/lists/*

# 安装rclone
RUN curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip \
    && unzip rclone-current-linux-amd64.zip \
    && cp rclone-*/rclone /usr/bin/ \
    && chmod +x /usr/bin/rclone \
    && rm -rf rclone-*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/logs /app/config /app/data /app/state

# 设置权限
RUN chmod +x /app/*.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "
import sys
sys.path.insert(0, '/app')
from core.agent import ProxyAgent
import json

try:
    with open('/app/config/config.json', 'r') as f:
        config = json.load(f)
    agent = ProxyAgent(config)
    if agent.is_healthy():
        exit(0)
    else:
        exit(1)
except Exception as e:
    exit(1)
"

# 启动命令
CMD ["python", "proxy.py", "--config", "/app/config/config.json"]