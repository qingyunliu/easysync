#!/bin/bash

# 设置Go环境变量
export GOOS=linux
export GOARCH=amd64
export CGO_ENABLED=0

# 编译
go build -o easysync-agent ./cmd/agent

# 检查编译结果
if [ $? -eq 0 ]; then
    echo "编译成功"
    chmod +x easysync-agent
else
    echo "编译失败"
    exit 1
fi 