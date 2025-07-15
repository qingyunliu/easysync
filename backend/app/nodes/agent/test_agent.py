#!/usr/bin/env python3
"""
测试代理agent的功能
"""

import json
import logging
import time
from core.agent import ProxyAgent

def test_agent():
    """测试代理agent"""
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置
    config = {
        'server': {
            'host': 'localhost',
            'port': 5000
        },
        'node': {
            'user': 1,  # 默认用户ID
            'id': None,  # 初始化时为空，注册后获得
            'token': None  # 初始化时为空，注册后获得
        },
        'heartbeat_interval': 30,
        'task_poll_interval': 10,
        'version': '1.0.0',
        'state_dir': 'state',
        'log_dir': 'logs',
        'monitoring': {
            'enabled': True,
            'interval': 60
        },
        'sync': {
            'max_retries': 3,
            'retry_delay': 5,
            'max_concurrent': 1
        }
    }
    
    try:
        # 创建并启动agent
        agent = ProxyAgent(config)
        agent.start()
        
        print(f"Agent启动成功，Node ID: {agent.node_id}")
        print(f"Token: {agent.token}")
        print("Agent正在运行...")
        
        # 等待用户中断
        agent.wait()
        
    except Exception as e:
        print(f"Agent启动失败: {e}")
        logging.error(f"Agent启动失败: {e}")

if __name__ == '__main__':
    test_agent()