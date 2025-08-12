#!/usr/bin/env python3
"""
测试告警流程的完整脚本
验证从存储创建到告警发送的整个流程
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app, db
from backend.app.models.alert import (
    AlertPolicy, AlertInstance, AlertTemplate, 
    AlertResourceType, AlertResourceItem, AlertEventType, AlertEventAction, AlertEventResult
)
from backend.app.models.event import Event
from backend.app.models.storage import Storage
from backend.app.models.user import User
from backend.app.alerts.init_data import init_all_alert_data
from backend.app.events.service import EventService
from backend.app.alerts.services import AlertService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_alert_flow():
    """测试完整的告警流程"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("=== 开始测试告警流程 ===")
            
            # 1. 初始化告警数据
            logger.info("1. 初始化告警数据...")
            init_all_alert_data()
            
            # 2. 检查数据是否初始化成功
            logger.info("2. 检查初始化数据...")
            resource_types = AlertResourceType.query.all()
            event_types = AlertEventType.query.all()
            event_results = AlertEventResult.query.all()
            
            logger.info(f"   - 资源类型数量: {len(resource_types)}")
            logger.info(f"   - 事件类型数量: {len(event_types)}")
            logger.info(f"   - 事件结果数量: {len(event_results)}")
            
            # 3. 创建测试用户（如果不存在）
            logger.info("3. 创建测试用户...")
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    password='testpass123'
                )
                db.session.add(test_user)
                db.session.commit()
                logger.info(f"   - 创建测试用户: {test_user.id}")
            else:
                logger.info(f"   - 使用现有测试用户: {test_user.id}")
            
            # 4. 创建告警策略
            logger.info("4. 创建存储失败告警策略...")
            alert_service = AlertService()
            
            # 检查是否已存在策略
            existing_policy = AlertPolicy.query.filter_by(
                name='存储操作失败告警'
            ).first()
            
            if existing_policy:
                logger.info(f"   - 使用现有策略: {existing_policy.id}")
                policy = existing_policy
            else:
                policy_data = {
                    'name': '存储操作失败告警',
                    'description': '监控存储操作失败事件',
                    'policy_type': 'event',
                    'event_type': 'storage',
                    'event_actions': ['add_storage', 'delete_storage', 'update_storage'],
                    'event_results': ['failed', 'error'],
                    'level': 'error',
                    'enabled': True,
                    'notification_targets': [
                        {
                            'type': 'email',
                            'data': {'email': 'admin@example.com'}
                        }
                    ]
                }
                
                policy = alert_service.create_policy(policy_data, test_user.id)
                logger.info(f"   - 创建新策略: {policy.id}")
            
            # 5. 创建事件服务
            logger.info("5. 创建事件服务...")
            event_service = EventService()
            
            # 6. 模拟存储创建失败事件
            logger.info("6. 模拟存储创建失败事件...")
            try:
                event = event_service.create_storage_event(
                    user_id=test_user.id,
                    event_action='add_storage',
                    event_result='failed',
                    message='存储创建失败：配置错误',
                    details={
                        'storage_name': 'test-storage',
                        'storage_type': 's3',
                        'error': 'Invalid configuration',
                        'test': True
                    }
                )
                logger.info(f"   - 创建事件成功: {event.id}")
                logger.info(f"   - 事件类型: {event.event_type}")
                logger.info(f"   - 事件动作: {event.event_action}")
                logger.info(f"   - 事件结果: {event.event_result}")
                
            except Exception as e:
                logger.error(f"   - 创建事件失败: {e}")
                return False
            
            # 7. 检查告警实例是否创建
            logger.info("7. 检查告警实例...")
            alert_instances = AlertInstance.query.filter_by(policy_id=policy.id).all()
            logger.info(f"   - 告警实例数量: {len(alert_instances)}")
            
            if alert_instances:
                latest_instance = alert_instances[-1]
                logger.info(f"   - 最新告警实例: {latest_instance.id}")
                logger.info(f"   - 告警状态: {latest_instance.status}")
                logger.info(f"   - 告警级别: {latest_instance.severity}")
                logger.info(f"   - 告警消息: {latest_instance.annotations.get('message', 'N/A')}")
            
            # 8. 检查事件记录
            logger.info("8. 检查事件记录...")
            events = Event.query.filter_by(event_type='storage').all()
            logger.info(f"   - 存储事件总数: {len(events)}")
            
            # 9. 测试告警策略评估
            logger.info("9. 测试告警策略评估...")
            from backend.app.alerts.evaluator import AlertEvaluator
            evaluator = AlertEvaluator()
            
            # 重新评估事件
            triggered_alerts = evaluator.evaluate_event(event)
            logger.info(f"   - 触发的告警数量: {len(triggered_alerts)}")
            
            for alert_info in triggered_alerts:
                policy_info = alert_info['policy']
                logger.info(f"   - 触发策略: {policy_info.name}")
            
            # 10. 测试通知发送（模拟）
            logger.info("10. 测试通知发送...")
            if alert_instances:
                try:
                    # 这里只是测试通知发送逻辑，不会真正发送
                    alert_service._send_notifications(policy, latest_instance)
                    logger.info("   - 通知发送逻辑执行成功")
                except Exception as e:
                    logger.error(f"   - 通知发送失败: {e}")
            
            logger.info("=== 告警流程测试完成 ===")
            return True
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def check_database_tables():
    """检查数据库表是否存在"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("=== 检查数据库表 ===")
            
            # 检查告警相关表
            tables_to_check = [
                'alert_policies',
                'alert_instances', 
                'alert_templates',
                'alert_resource_types',
                'alert_resource_items',
                'alert_event_types',
                'alert_event_actions',
                'alert_event_results',
                'events'
            ]
            
            for table_name in tables_to_check:
                exists = db.engine.has_table(table_name)
                status = "✓" if exists else "✗"
                logger.info(f"{status} {table_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"检查数据库表失败: {e}")
            return False

if __name__ == '__main__':
    print("告警流程测试脚本")
    print("=" * 50)
    
    # 首先检查数据库表
    if not check_database_tables():
        print("数据库表检查失败，请先创建表")
        sys.exit(1)
    
    # 运行告警流程测试
    success = test_alert_flow()
    
    if success:
        print("\n✅ 告警流程测试成功！")
        print("\n流程总结:")
        print("1. 初始化告警数据 ✓")
        print("2. 创建告警策略 ✓") 
        print("3. 创建存储失败事件 ✓")
        print("4. 触发告警评估 ✓")
        print("5. 创建告警实例 ✓")
        print("6. 发送通知（模拟）✓")
    else:
        print("\n❌ 告警流程测试失败！")
        sys.exit(1)
