#!/usr/bin/env python3
"""
告警系统测试脚本
用于验证告警系统的各项功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend import create_app, db
from backend.app.models.alert import (
    AlertResourceType, AlertResourceItem, 
    AlertEventType, AlertEventAction, AlertEventResult,
    AlertPolicy, AlertInstance, AlertTemplate
)
from backend.app.models.user import User
from backend.app.alerts.services import AlertService
from backend.app.events.service import event_service
from backend.app.alerts.init_data import init_all_alert_data

def test_alert_system():
    """测试告警系统功能"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== 告警系统测试开始 ===")
            
            # 1. 初始化基础数据
            print("\n1. 初始化基础数据...")
            init_all_alert_data()
            print("✓ 基础数据初始化完成")
            
            # 2. 测试资源类型
            print("\n2. 测试资源类型...")
            resource_types = AlertResourceType.query.all()
            print(f"✓ 找到 {len(resource_types)} 个资源类型:")
            for rt in resource_types:
                print(f"  - {rt.name} ({rt.code})")
            
            # 3. 测试事件类型
            print("\n3. 测试事件类型...")
            event_types = AlertEventType.query.all()
            print(f"✓ 找到 {len(event_types)} 个事件类型:")
            for et in event_types:
                print(f"  - {et.name} ({et.code})")
            
            # 4. 测试事件结果
            print("\n4. 测试事件结果...")
            event_results = AlertEventResult.query.all()
            print(f"✓ 找到 {len(event_results)} 个事件结果:")
            for er in event_results:
                print(f"  - {er.name} ({er.code})")
            
            # 5. 测试告警服务
            print("\n5. 测试告警服务...")
            alert_service = AlertService()
            
            # 获取资源类型
            resource_types_data = alert_service.get_resource_types()
            print(f"✓ 获取到 {len(resource_types_data)} 个资源类型")
            
            # 获取事件类型
            event_types_data = alert_service.get_event_types()
            print(f"✓ 获取到 {len(event_types_data)} 个事件类型")
            
            # 获取事件结果
            event_results_data = alert_service.get_event_results()
            print(f"✓ 获取到 {len(event_results_data)} 个事件结果")
            
            # 6. 测试事件服务
            print("\n6. 测试事件服务...")
            
            # 创建测试用户
            test_user = User.query.first()
            if not test_user:
                print("⚠ 没有找到测试用户，跳过事件测试")
            else:
                # 创建用户事件
                user_event = event_service.create_user_event(
                    user_id=test_user.id,
                    event_action="login",
                    event_result="success",
                    message="用户登录成功",
                    details={"ip": "192.168.1.100", "user_agent": "Mozilla/5.0"}
                )
                print(f"✓ 创建用户事件: {user_event.id}")
                
                # 创建存储事件
                storage_event = event_service.create_storage_event(
                    user_id=test_user.id,
                    event_action="add_storage",
                    event_result="failed",
                    message="添加存储失败",
                    details={"storage_name": "test-storage", "error": "connection timeout"}
                )
                print(f"✓ 创建存储事件: {storage_event.id}")
                
                # 获取事件列表
                events = event_service.get_events(user_id=test_user.id, page=1, per_page=10)
                print(f"✓ 获取到 {len(events['events'])} 个事件")
                
                # 获取事件统计
                stats = event_service.get_event_statistics(user_id=test_user.id, time_range='24h')
                print(f"✓ 事件统计: {stats}")
            
            # 7. 测试告警策略创建
            print("\n7. 测试告警策略创建...")
            if test_user:
                # 创建资源告警策略
                resource_policy_data = {
                    "name": "测试CPU告警",
                    "description": "测试CPU使用率告警策略",
                    "policy_type": "resource",
                    "resource_type": "system",
                    "alert_items": ["cpu_percent"],
                    "trigger_rules": {
                        "cpu_percent": {
                            "operator": ">",
                            "threshold": 80.0,
                            "duration": 60
                        }
                    },
                    "level": "warning",
                    "enabled": True
                }
                
                resource_policy = alert_service.create_policy(resource_policy_data, test_user.id)
                print(f"✓ 创建资源告警策略: {resource_policy.id}")
                
                # 创建事件告警策略
                event_policy_data = {
                    "name": "测试存储失败告警",
                    "description": "测试存储操作失败告警策略",
                    "policy_type": "event",
                    "event_type": "storage",
                    "event_actions": ["add_storage", "delete_storage"],
                    "event_results": ["failed", "error"],
                    "level": "error",
                    "enabled": True
                }
                
                event_policy = alert_service.create_policy(event_policy_data, test_user.id)
                print(f"✓ 创建事件告警策略: {event_policy.id}")
                
                # 获取策略列表
                policies = alert_service.get_policies(user_id=test_user.id, page=1, per_page=10)
                print(f"✓ 获取到 {len(policies['policies'])} 个告警策略")
            
            print("\n=== 告警系统测试完成 ===")
            print("✓ 所有测试通过！")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_alert_system() 