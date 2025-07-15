#!/bin/bash

# EasySync 前端启动脚本

echo "🚀 启动 EasySync 前端应用..."

# 检查是否存在 node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖包..."
    npm install
fi

# 检查是否存在 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告：未找到 .env 文件，使用默认配置"
    echo "请确保后端服务运行在 http://localhost:5000"
fi

# 启动开发服务器
echo "🌐 启动开发服务器..."
npm run dev

echo "✅ 前端应用已启动！"
echo "🔗 访问地址：http://localhost:5173"
echo "📄 确保后端服务运行在：http://localhost:5000"