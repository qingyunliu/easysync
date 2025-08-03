#!/usr/bin/env python3
"""
告警系统测试脚本
测试告警策略、通知渠道和通知对象的功能
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5000/api"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN_HERE"  # 需要替换为实际的token
}

def test_alert_system():
    """测试告警系统功能"""
    print("=== 告警系统功能测试 ===\n")
    
    # 1. 测试创建通知渠道
    print("1. 测试创建通知渠道...")
    channel_data = {
        "name": "测试邮件渠道",
        "channel_type": "email",
        "enabled": True,
        "retry_count": 3,
        "rate_limit": 100,
        "timeout": 30,
        "is_default": True,
        "config": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/alerts/channels", 
                               headers=HEADERS, 
                               json=channel_data)
        if response.status_code == 201:
            channel = response.json()["channel"]
            print(f"✓ 通知渠道创建成功: {channel['name']}")
            channel_id = channel["id"]
        else:
            print(f"✗ 通知渠道创建失败: {response.text}")
            return
    except Exception as e:
        print(f"✗ 通知渠道创建异常: {e}")
        return
    
    # 2. 测试创建通知对象
    print("\n2. 测试创建通知对象...")
    target_data = {
        "name": "测试通知对象",
        "target_type": "email",
        "enabled": True,
        "description": "测试用的通知对象",
        "alert_policies": [],
        "channels": [channel_id],
        "target_config": {
            "email": "admin@example.com"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/alerts/targets", 
                               headers=HEADERS, 
                               json=target_data)
        if response.status_code == 201:
            target = response.json()["target"]
            print(f"✓ 通知对象创建成功: {target['name']}")
            target_id = target["id"]
        else:
            print(f"✗ 通知对象创建失败: {response.text}")
            return
    except Exception as e:
        print(f"✗ 通知对象创建异常: {e}")
        return
    
    # 3. 测试创建资源告警策略
    print("\n3. 测试创建资源告警策略...")
    resource_policy_data = {
        "name": "CPU使用率告警",
        "description": "监控CPU使用率，超过80%时告警",
        "level": "warning",
        "policy_type": "resource",
        "enabled": True,
        "resource_type": "system",
        "monitored_resources": ["system"],
        "alert_items": ["CPU"],
        "trigger_rules": {
            "CPU": {
                "operator": ">",
                "threshold": 80,
                "duration": 300
            }
        },
        "notification_targets": [target_id]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/alerts/policies", 
                               headers=HEADERS, 
                               json=resource_policy_data)
        if response.status_code == 201:
            policy = response.json()["policy"]
            print(f"✓ 资源告警策略创建成功: {policy['name']}")
            resource_policy_id = policy["id"]
        else:
            print(f"✗ 资源告警策略创建失败: {response.text}")
            return
    except Exception as e:
        print(f"✗ 资源告警策略创建异常: {e}")
        return
    
    # 3.1. 测试创建事件告警策略
    print("\n3.1. 测试创建事件告警策略...")
    event_policy_data = {
        "name": "存储操作失败告警",
        "description": "监控存储操作失败事件",
        "level": "error",
        "policy_type": "event",
        "enabled": True,
        "event_type": "storage",
        "event_actions": ["create", "delete", "update"],
        "event_results": ["failed", "error"],
        "notification_targets": [target_id]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/alerts/policies", 
                               headers=HEADERS, 
                               json=event_policy_data)
        if response.status_code == 201:
            policy = response.json()["policy"]
            print(f"✓ 事件告警策略创建成功: {policy['name']}")
            event_policy_id = policy["id"]
        else:
            print(f"✗ 事件告警策略创建失败: {response.text}")
            return
    except Exception as e:
        print(f"✗ 事件告警策略创建异常: {e}")
        return
    
    try:
        response = requests.post(f"{BASE_URL}/alerts/policies", 
                               headers=HEADERS, 
                               json=policy_data)
        if response.status_code == 201:
            policy = response.json()["policy"]
            print(f"✓ 告警策略创建成功: {policy['name']}")
            policy_id = policy["id"]
        else:
            print(f"✗ 告警策略创建失败: {response.text}")
            return
    except Exception as e:
        print(f"✗ 告警策略创建异常: {e}")
        return
    
    # 4. 测试获取告警策略列表
    print("\n4. 测试获取告警策略列表...")
    try:
        response = requests.get(f"{BASE_URL}/alerts/policies", headers=HEADERS)
        if response.status_code == 200:
            policies = response.json()["policies"]
            print(f"✓ 获取到 {len(policies)} 个告警策略")
            for policy in policies:
                print(f"  - {policy['name']} ({policy['policy_type']})")
        else:
            print(f"✗ 获取告警策略失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取告警策略异常: {e}")
    
    # 5. 测试获取通知渠道列表
    print("\n5. 测试获取通知渠道列表...")
    try:
        response = requests.get(f"{BASE_URL}/alerts/channels", headers=HEADERS)
        if response.status_code == 200:
            channels = response.json()["channels"]
            print(f"✓ 获取到 {len(channels)} 个通知渠道")
            for channel in channels:
                print(f"  - {channel['name']} ({channel['channel_type']})")
        else:
            print(f"✗ 获取通知渠道失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取通知渠道异常: {e}")
    
    # 6. 测试获取通知对象列表
    print("\n6. 测试获取通知对象列表...")
    try:
        response = requests.get(f"{BASE_URL}/alerts/targets", headers=HEADERS)
        if response.status_code == 200:
            targets = response.json()["targets"]
            print(f"✓ 获取到 {len(targets)} 个通知对象")
            for target in targets:
                print(f"  - {target['name']} ({target['target_type']})")
        else:
            print(f"✗ 获取通知对象失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取通知对象异常: {e}")
    
    # 7. 测试告警策略模板
    print("\n7. 测试获取告警策略模板...")
    try:
        response = requests.get(f"{BASE_URL}/alerts/templates", headers=HEADERS)
        if response.status_code == 200:
            templates = response.json()["templates"]
            print(f"✓ 获取到 {len(templates)} 个告警策略模板")
            for template in templates:
                print(f"  - {template['name']} ({template['policy_type']})")
        else:
            print(f"✗ 获取告警策略模板失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取告警策略模板异常: {e}")
    
    # 8. 测试获取可监控资源
    print("\n8. 测试获取可监控资源...")
    try:
        response = requests.get(f"{BASE_URL}/alerts/resources", headers=HEADERS)
        if response.status_code == 200:
            resources = response.json()["resources"]
            print("✓ 获取到可监控资源:")
            for resource_type, resource_list in resources.items():
                print(f"  - {resource_type}: {len(resource_list)} 个")
        else:
            print(f"✗ 获取可监控资源失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取可监控资源异常: {e}")
    
    # 9. 测试获取可监控事件
    print("\n9. 测试获取可监控事件...")
    try:
        response = requests.get(f"{BASE_URL}/alerts/events", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            events = data["events"]
            results = data["results"]
            print("✓ 获取到可监控事件:")
            for event_type, event_list in events.items():
                print(f"  - {event_type}: {len(event_list)} 个")
            print(f"  - 结果类型: {len(results)} 个")
            for result in results:
                print(f"    * {result['name']} ({result['id']})")
        else:
            print(f"✗ 获取可监控事件失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取可监控事件异常: {e}")
    
    print("\n=== 测试完成 ===")

def test_notification_system():
    """测试通知系统功能"""
    print("\n=== 通知系统功能测试 ===\n")
    
    # 测试发送通知
    print("测试发送通知...")
    notification_data = {
        "level": "warning",
        "title": "测试告警",
        "content": "这是一个测试告警消息",
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/notifications", 
                               headers=HEADERS, 
                               json=notification_data)
        if response.status_code == 200:
            print("✓ 测试通知发送成功")
        else:
            print(f"✗ 测试通知发送失败: {response.text}")
    except Exception as e:
        print(f"✗ 测试通知发送异常: {e}")

if __name__ == "__main__":
    print("告警系统测试脚本")
    print("请确保后端服务正在运行，并更新脚本中的TOKEN")
    print("=" * 50)
    
    # 检查服务是否可用
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务连接正常")
        else:
            print("✗ 后端服务连接异常")
            exit(1)
    except Exception as e:
        print(f"✗ 无法连接到后端服务: {e}")
        print("请确保后端服务正在运行在 http://localhost:5000")
        exit(1)
    
    # 运行测试
    test_alert_system()
    test_notification_system() 