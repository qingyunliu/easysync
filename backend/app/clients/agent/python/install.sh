#!/bin/bash

# 检查参数数量
if [ $# -lt 3 ]; then
    echo "Usage: $0 <server_ip> <client_id> <user_id>"
    echo "Example: $0 192.168.1.100 123 456"
    exit 1
fi

# 获取参数
SERVER_IP=$1
CLIENT_ID=$2
USER_ID=$3

# 验证参数
if [ -z "$SERVER_IP" ]; then
    echo "Error: Server IP cannot be empty"
    exit 1
fi

if [ -z "$CLIENT_ID" ]; then
    echo "Error: Client ID cannot be empty"
    exit 1
fi

if [ -z "$USER_ID" ]; then
    echo "Error: User ID cannot be empty"
    exit 1
fi

# 设置安装目录
INSTALL_DIR="/opt/easysync/agent"
BACKUP_DIR="/opt/easysync/backups"
LOG_DIR="/var/log/easysync"

# 创建必要的目录
mkdir -p $INSTALL_DIR
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR

# 安装 Python 依赖
pip install -r requirements.txt

# 设置配置文件
cat > $INSTALL_DIR/config.yaml << EOF
client:
  id: "${CLIENT_ID}"
  version: "1.0.0"
  name: "Agent Client"
  description: "Agent client for EasySync"
  user_id: "${USER_ID}"

server:
  url: "http://${SERVER_IP}:5001"
  ws_path: "/ws/socket.io"
  heartbeat_interval: 30

monitor:
  interval: 10
  metrics:
    - cpu
    - memory
    - disk
    - network

# 同步配置
sync:
  max_retries: 3 # 最大重试次数
  retry_interval: 5s # 重试间隔
  default_timeout: 30s # 默认超时时间

# 日志配置
log:
  level: "INFO"
  directory: "logs"
  max_size: 10485760 # 10MB
  backup_count: 5
  filename: "agent.log"

upgrade:
  url: "http://${SERVER_IP}:5001/upgrade"
  backup_dir: "$BACKUP_DIR"
  check_interval: 3600  # 1小时检查一次更新
EOF

# 设置启动脚本
cat > /etc/init.d/easysync-agent << EOF
#!/bin/bash
# chkconfig: 2345 90 10
# description: EasySync Agent Service

case "\$1" in
    start)
        echo "Starting EasySync Agent..."
        cd $INSTALL_DIR
        python3 client.py &
        ;;
    stop)
        echo "Stopping EasySync Agent..."
        pkill -f "python3 client.py"
        ;;
    restart)
        \$0 stop
        sleep 2
        \$0 start
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart}"
        exit 1
        ;;
esac

exit 0
EOF

# 设置权限
chmod +x /etc/init.d/easysync-agent
chmod +x $INSTALL_DIR/client.py

# 添加到系统服务
if command -v systemctl &> /dev/null; then
    # Systemd
    cat > /etc/systemd/system/easysync-agent.service << EOF
[Unit]
Description=EasySync Agent Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable easysync-agent
    systemctl start easysync-agent
else
    # SysV init
    chkconfig --add easysync-agent
    chkconfig easysync-agent on
    service easysync-agent start
fi

echo "EasySync Agent installation completed!" 