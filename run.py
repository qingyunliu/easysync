#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app

# 创建Flask应用
app = create_app()

if __name__ == '__main__':
    # 开发模式启动
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )