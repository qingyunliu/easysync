#!/bin/bash
# EasySync Frontend 启动脚本

# 设置项目根目录
PROJECT_ROOT="/root/git-easysync/easysync/frontend"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "启动 EasySync 前端服务"
echo "=========================================="
echo "项目目录: $PROJECT_ROOT"
echo "Node版本: $(node --version)"
echo "NPM版本: $(npm --version)"
echo "=========================================="
echo ""

# 显式加载.env文件
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ 环境变量已加载"
    echo "  - API地址: $VITE_API_URL"
    echo "  - WebSocket: $VITE_WS_URL"
else
    echo "✗ 未找到 .env 文件"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "✗ 依赖未安装，正在安装..."
    npm install
    if [ $? -ne 0 ]; then
        echo "✗ 依赖安装失败"
        exit 1
    fi
    echo "✓ 依赖安装完成"
else
    echo "✓ 依赖已安装"
fi

echo ""
echo "=========================================="
echo "启动开发服务器..."
echo "=========================================="
echo "访问地址: http://localhost:3000"
echo "API地址: $VITE_API_URL"
echo "=========================================="
echo ""

# 启动开发服务器
npm run dev