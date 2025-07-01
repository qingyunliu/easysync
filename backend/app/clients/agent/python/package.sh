#!/bin/bash

# 设置版本号
VERSION=1.0.0
PACKAGE_NAME=easysync-agent

# 获取当前目录
CURRENT_DIR=$(pwd)

# 创建临时目录
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR=${TEMP_DIR}/${PACKAGE_NAME}

# 创建包目录结构
mkdir -p ${PACKAGE_DIR}
mkdir -p ${PACKAGE_DIR}/modules

# 复制文件
cp client.py ${PACKAGE_DIR}/
cp config.yaml ${PACKAGE_DIR}/
cp requirements.txt ${PACKAGE_DIR}/
cp install.sh ${PACKAGE_DIR}/
cp modules/config.py modules/heartbeat.py modules/logger.py modules/monitor.py modules/task.py modules/upgrade.py ${PACKAGE_DIR}/modules/
echo ${VERSION} > ${PACKAGE_DIR}/version.txt

# 设置安装脚本权限
chmod +x ${PACKAGE_DIR}/install.sh

# 打包
cd ${TEMP_DIR}
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}

# 移动包到当前目录
mv "${PACKAGE_NAME}.tar.gz" "${CURRENT_DIR}/"

# 清理临时目录
rm -rf ${TEMP_DIR}

echo "Package created: ${PACKAGE_NAME}.tar.gz" 