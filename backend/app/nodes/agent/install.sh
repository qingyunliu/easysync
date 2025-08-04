#!/bin/bash

# 检查参数数量
if [ $# -lt 3 ]; then
    echo "Usage: $0 <server_ip> <node_id> <user_id>"
    echo "Example: $0 192.168.1.100 123 456"
    exit 1
fi

# 获取参数
SERVER_IP=$1
NODE_ID=$2
USER_ID=$3

# 验证参数
if [ -z "$SERVER_IP" ]; then
    echo "Error: Server IP cannot be empty"
    exit 1
fi

if [ -z "$NODE_ID" ]; then
    echo "Error: Node ID cannot be empty"
    exit 1
fi

if [ -z "$USER_ID" ]; then
    echo "Error: User ID cannot be empty"
    exit 1
fi

# 设置安装目录
INSTALL_DIR="/opt/easysync/proxy"
BACKUP_DIR="/opt/easysync/backups"
LOG_DIR="/var/log/easysync"

# 创建必要的目录
mkdir -p $INSTALL_DIR
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR

# 安装 Python 依赖
pip install -r requirements.txt

# 设置配置文件
cat > $INSTALL_DIR/config/config.json << EOF
{
    "server": {
        "host": "${SERVER_IP}",
        "port": 5000
    },
    "node": {
        "id": "${NODE_ID}",
        "user": "${USER_ID}",
        "token": ""
    },
    "heartbeat_interval": 30,
    "monitor": {
        "interval": 5,
        "max_history": 1000,
        "alert_thresholds": {
            "cpu_percent": 90,
            "memory_percent": 90,
            "disk_percent": 90
        }
    },
    "sync": {
        "max_retries": 3,
        "retry_delay": 5,
        "max_concurrent": 3
    },
    "state_dir": "state",
    "log_level": "INFO"
} 
EOF

# 设置启动脚本
cat > /etc/init.d/easysync-proxy << EOF
#!/bin/bash
# chkconfig: 2345 90 10
# description: EasySync Proxy Agent Service

case "\$1" in
    start)
        echo "Starting EasySync Proxy Agent..."
        cd $INSTALL_DIR
        python3 client.py --config /opt/easysync/proxy/config/config.json &
        ;;
    stop)
        echo "Stopping EasySync Proxy Agent..."
        pkill -f "python3 proxy.py --config /opt/easysync/proxy/config/config.json"
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
chmod +x /etc/init.d/easysync-proxy
chmod +x $INSTALL_DIR/proxy.py

# 添加到系统服务
if command -v systemctl &> /dev/null; then
    # Systemd
    cat > /etc/systemd/system/easysync-proxy.service << EOF
[Unit]
Description=EasySync Proxy Agent Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/proxy.py --config /opt/easysync/proxy/config/config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable easysync-proxy
    systemctl start easysync-proxy
else
    # SysV init
    chkconfig --add easysync-proxy
    chkconfig easysync-proxy on
    service easysync-proxy start
fi

echo "EasySync Proxy Agent installation completed!" 