#!/usr/bin/env python3
"""
增强版代理agent测试脚本
"""

import json
import time
import sys
import os
from datetime import datetime
from core.agent import ProxyAgent
from utils.logger import get_log_manager

def test_enhanced_agent():
    """测试增强版代理agent"""
    
    # 使用统一的日志管理器
    log_manager = get_log_manager()
    logger = log_manager.get_logger('AgentTest')
    
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
    
    try:
        # 创建并启动agent
        agent = ProxyAgent(config)
        
        print("="*50)
        print("EasySync Enhanced Agent 启动中...")
        print("="*50)
        
        agent.start()
        
        print(f"Agent启动成功！")
        print(f"Node ID: {agent.node_id}")
        print(f"Token: {agent.token}")
        print(f"Version: {agent.version}")
        print(f"Server URL: {agent.server_comm.server_url}")
        
        # 等待一段时间让agent完成初始化
        time.sleep(5)
        
        # 显示agent状态
        print("\n" + "="*50)
        print("Agent状态信息:")
        print("="*50)
        status = agent.get_agent_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # 测试存储连接检查功能
        print("\n" + "="*50)
        print("测试存储连接检查:")
        print("="*50)
        
        # 测试本地存储连接
        local_storage_config = {
            'id': 'test_local',
            'type': 'local',
            'config': {
                'base_path': '/tmp'
            }
        }
        
        print("检查本地存储连接...")
        result = agent.check_storage_connection(local_storage_config)
        print(f"结果: {result.status.value}")
        print(f"消息: {result.message}")
        print(f"响应时间: {result.response_time:.2f}秒")
        
        # 测试挂载检查功能
        print("\n" + "="*50)
        print("测试挂载检查:")
        print("="*50)
        
        print("检查 /tmp 挂载状态...")
        mount_result = agent.check_mount_status('/tmp')
        print(f"结果: {mount_result.status.value}")
        print(f"挂载点: {mount_result.mount_point}")
        print(f"是否挂载: {mount_result.is_mounted}")
        
        # 显示功能特性
        print("\n" + "="*50)
        print("新增功能特性:")
        print("="*50)
        features = [
            "✅ 任务取消和暂停/恢复",
            "✅ 任务验证和重试机制",
            "✅ 详细进度跟踪和上报",
            "✅ 存储连接检查",
            "✅ 挂载状态检查",
            "✅ 增强的错误处理",
            "✅ 任务状态管理",
            "✅ 进度历史记录",
            "✅ 健康状态监控",
            "✅ 配置验证"
        ]
        
        for feature in features:
            print(feature)
        
        print("\n" + "="*50)
        print("Agent正在运行...")
        print("按 Ctrl+C 停止")
        print("="*50)
        
        # 等待用户中断
        agent.wait()
        
    except KeyboardInterrupt:
        print("\n收到停止信号，正在关闭Agent...")
        if 'agent' in locals():
            agent.stop()
        print("Agent已停止")
        
    except Exception as e:
        print(f"Agent启动失败: {e}")
        logger.error(f"Agent启动失败: {e}")
        import traceback
        traceback.print_exc()

def show_usage():
    """显示使用说明"""
    print("""
EasySync Enhanced Agent 测试工具

使用方法:
    python test_enhanced_agent.py

功能特性:
    - 任务取消、暂停、恢复
    - 任务验证和重试
    - 详细进度跟踪
    - 存储连接检查
    - 挂载状态检查
    - 增强的错误处理
    - 健康状态监控

配置说明:
    请确保服务器端正在运行，并且配置正确的服务器地址和端口

日志输出:
    - 控制台输出: 实时日志
    - 文件输出: agent_test.log

""")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_usage()
    else:
        test_enhanced_agent()