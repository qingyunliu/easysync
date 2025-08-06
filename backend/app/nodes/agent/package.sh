#!/bin/bash
# package.sh
set -e

WORKDIR=$(cd $(dirname $0); pwd)
cd "$WORKDIR"

PKG_NAME="easysync-proxy"
PKG_FILE="${PKG_NAME}.tar.gz"

echo "打包 SyncProxy-Agent..."

# 清理旧包
rm -f "$PKG_FILE"

# 打包（排除pyc、__pycache__等无用文件）
tar --exclude="*.pyc" --exclude="._*" --exclude=".DS_Store" --exclude="__pycache__" -czvf "$PKG_FILE" ./*

echo "打包完成: $PKG_FILE"