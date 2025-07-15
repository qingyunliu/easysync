#!/usr/bin/env python3
"""
增强版代理agent测试脚本
"""

import json
import logging
import time
import sys
import os
from datetime import datetime
from core.agent import ProxyAgent

def test_enhanced_agent():
    """测试增强版代理agent"""
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('agent_test.log')
        ]
    )
    
    logger = logging.getLogger('AgentTest')
    
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
        },
        'task_manager': {
            'max_retries': 3,
            'retry_delay': 5,
            'task_timeout': 3600
        },
        'connection_check': {
            'timeout': 30,
            'retry_count': 3,
            'retry_delay': 2
        },
        'progress': {
            'report_interval': 5,
            'detailed_logging': True,
            'max_history_size': 100
        }
    }
    
    try:\n        # 创建并启动agent\n        agent = ProxyAgent(config)\n        \n        print(\"=\"*50)\n        print(\"EasySync Enhanced Agent 启动中...\")\n        print(\"=\"*50)\n        \n        agent.start()\n        \n        print(f\"Agent启动成功！\")\n        print(f\"Node ID: {agent.node_id}\")\n        print(f\"Token: {agent.token}\")\n        print(f\"Version: {agent.version}\")\n        print(f\"Server URL: {agent.server_comm.server_url}\")\n        \n        # 等待一段时间让agent完成初始化\n        time.sleep(5)\n        \n        # 显示agent状态\n        print(\"\\n\" + \"=\"*50)\n        print(\"Agent状态信息:\")\n        print(\"=\"*50)\n        status = agent.get_agent_status()\n        print(json.dumps(status, indent=2, ensure_ascii=False))\n        \n        # 测试存储连接检查功能\n        print(\"\\n\" + \"=\"*50)\n        print(\"测试存储连接检查:\")\n        print(\"=\"*50)\n        \n        # 测试本地存储连接\n        local_storage_config = {\n            'id': 'test_local',\n            'type': 'local',\n            'config': {\n                'base_path': '/tmp'\n            }\n        }\n        \n        print(\"检查本地存储连接...\")\n        result = agent.check_storage_connection(local_storage_config)\n        print(f\"结果: {result.status.value}\")\n        print(f\"消息: {result.message}\")\n        print(f\"响应时间: {result.response_time:.2f}秒\")\n        \n        # 测试挂载检查功能\n        print(\"\\n\" + \"=\"*50)\n        print(\"测试挂载检查:\")\n        print(\"=\"*50)\n        \n        print(\"检查 /tmp 挂载状态...\")\n        mount_result = agent.check_mount_status('/tmp')\n        print(f\"结果: {mount_result.status.value}\")\n        print(f\"挂载点: {mount_result.mount_point}\")\n        print(f\"是否挂载: {mount_result.is_mounted}\")\n        \n        # 显示功能特性\n        print(\"\\n\" + \"=\"*50)\n        print(\"新增功能特性:\")\n        print(\"=\"*50)\n        features = [\n            \"✅ 任务取消和暂停/恢复\",\n            \"✅ 任务验证和重试机制\",\n            \"✅ 详细进度跟踪和上报\",\n            \"✅ 存储连接检查\",\n            \"✅ 挂载状态检查\",\n            \"✅ 增强的错误处理\",\n            \"✅ 任务状态管理\",\n            \"✅ 进度历史记录\",\n            \"✅ 健康状态监控\",\n            \"✅ 配置验证\"\n        ]\n        \n        for feature in features:\n            print(feature)\n        \n        print(\"\\n\" + \"=\"*50)\n        print(\"Agent正在运行...\")\n        print(\"按 Ctrl+C 停止\")\n        print(\"=\"*50)\n        \n        # 等待用户中断\n        agent.wait()\n        \n    except KeyboardInterrupt:\n        print(\"\\n收到停止信号，正在关闭Agent...\")\n        if 'agent' in locals():\n            agent.stop()\n        print(\"Agent已停止\")\n        \n    except Exception as e:\n        print(f\"Agent启动失败: {e}\")\n        logger.error(f\"Agent启动失败: {e}\")\n        import traceback\n        traceback.print_exc()\n\ndef show_usage():\n    \"\"\"显示使用说明\"\"\"\n    print(\"\"\"\nEasySync Enhanced Agent 测试工具\n\n使用方法:\n    python test_enhanced_agent.py\n\n功能特性:\n    - 任务取消、暂停、恢复\n    - 任务验证和重试\n    - 详细进度跟踪\n    - 存储连接检查\n    - 挂载状态检查\n    - 增强的错误处理\n    - 健康状态监控\n\n配置说明:\n    请确保服务器端正在运行，并且配置正确的服务器地址和端口\n\n日志输出:\n    - 控制台输出: 实时日志\n    - 文件输出: agent_test.log\n\n\"\"\")\n\nif __name__ == '__main__':\n    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:\n        show_usage()\n    else:\n        test_enhanced_agent()