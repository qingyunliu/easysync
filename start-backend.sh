#!/bin/bash
# EasySync Backend 启动脚本

# 设置项目根目录
PROJECT_ROOT="/root/git-easysync/easysync"
cd "$PROJECT_ROOT"

# 加载环境变量配置
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "✓ 环境变量已加载"
else
    echo "✗ 未找到 .env 文件"
    exit 1
fi

# 激活虚拟环境
source backend/venv/bin/activate
echo "✓ Python 虚拟环境已激活"

# 创建必要的目录
mkdir -p uploads logs
echo "✓ 目录已创建"

# 启动后端服务
echo ""
echo "=========================================="
echo "启动 EasySync 后端服务"
echo "=========================================="
echo "访问地址: http://localhost:5000"
echo "API 文档: http://localhost:5000/api"
echo "数据库: SQLite (easysync.db)"
echo "=========================================="
echo ""

# 使用 Flask 开发服务器启动
export FLASK_APP=run.py
export FLASK_ENV=development

python3 run.py