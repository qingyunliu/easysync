#!/usr/bin/env python3
"""
EasySync 完整系统测试脚本
测试任务管理、proxy agent、连接测试等功能
"""

import requests
import json
import time
import threading
from datetime import datetime

class EasySyncTester:
    def __init__(self, server_url="http://localhost:5000", username="admin", password="admin"):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.token = None
        self.test_results = []
        
    def login(self):
        """登录获取JWT token"""
        try:
            response = requests.post(f"{self.server_url}/api/auth/login", json={
                "username": self.username,
                "password": self.password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.log_result("✅ 登录成功", True)
                return True
            else:
                self.log_result(f"❌ 登录失败: {response.status_code}", False)
                return False
                
        except Exception as e:
            self.log_result(f"❌ 登录异常: {e}", False)
            return False
    
    def get_headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_task_crud(self):
        """测试任务CRUD操作"""
        print("\n🔧 测试任务CRUD操作...")
        
        # 1. 创建任务
        task_data = {
            "name": "测试同步任务",
            "description": "系统测试任务",
            "type": "sync",
            "priority": 2,
            "source_type": "storage",
            "source_storage_id": 1,
            "source_path": "/data/source",
            "target_storage_id": 2,
            "target_path": "/backup/target",
            "options": {
                "delete": False,
                "checksum": True
            }
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/tasks",
                json=task_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 201:
                task = response.json()['data']
                task_id = task['id']
                self.log_result("✅ 创建任务成功", True)
                
                # 2. 获取任务详情
                response = requests.get(
                    f"{self.server_url}/api/tasks/{task_id}",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    self.log_result("✅ 获取任务详情成功", True)
                else:
                    self.log_result(f"❌ 获取任务详情失败: {response.status_code}", False)
                
                # 3. 启动任务
                response = requests.post(
                    f"{self.server_url}/api/tasks/{task_id}/start",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    self.log_result("✅ 启动任务成功", True)
                else:
                    self.log_result(f"❌ 启动任务失败: {response.status_code}", False)
                
                # 4. 取消任务
                time.sleep(2)  # 等待一下
                response = requests.post(
                    f"{self.server_url}/api/tasks/{task_id}/cancel",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    self.log_result("✅ 取消任务成功", True)
                else:
                    self.log_result(f"❌ 取消任务失败: {response.status_code}", False)
                
                # 5. 删除任务
                response = requests.delete(
                    f"{self.server_url}/api/tasks/{task_id}",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    self.log_result("✅ 删除任务成功", True)
                else:
                    self.log_result(f"❌ 删除任务失败: {response.status_code}", False)
                
            else:
                self.log_result(f"❌ 创建任务失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 任务CRUD测试异常: {e}", False)
    
    def test_connection_test(self):
        """测试连接测试功能"""
        print("\n🌐 测试连接测试功能...")
        
        # 测试本地存储连接
        storage_config = {
            "name": "测试本地存储",
            "type": "local",
            "config": {
                "base_path": "/tmp"
            }
        }
        
        try:
            # 首先获取可用节点
            nodes_response = requests.get(
                f"{self.server_url}/api/nodes",
                headers=self.get_headers()
            )
            
            if nodes_response.status_code != 200:
                self.log_result("❌ 获取节点列表失败", False)
                return
            
            available_nodes = [node for node in nodes_response.json()['data'] 
                             if node['status'] == 'online' and node['agent_status'] == 'running']
            
            if not available_nodes:
                self.log_result("❌ 没有可用的测试节点", False)
                return
            
            test_node = available_nodes[0]
            
            response = requests.post(
                f"{self.server_url}/api/storages/test-connection",
                json={
                    "type": storage_config["type"],
                    "config": storage_config["config"],
                    "node_id": test_node["id"]
                },
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                task = response.json()['data']
                self.log_result("✅ 创建连接测试任务成功", True)
                
                # 等待任务完成
                time.sleep(5)
                
                # 检查任务状态
                response = requests.get(
                    f"{self.server_url}/api/tasks/{task['task_id']}",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    updated_task = response.json()['data']
                    if updated_task['status'] in ['completed', 'failed']:
                        self.log_result(f"✅ 连接测试任务完成，状态: {updated_task['status']}", True)
                    else:
                        self.log_result(f"⏳ 连接测试任务进行中，状态: {updated_task['status']}", True)
                
            else:
                self.log_result(f"❌ 创建连接测试任务失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 连接测试异常: {e}", False)
    
    def test_task_statistics(self):
        """测试任务统计功能"""
        print("\n📊 测试任务统计功能...")
        
        try:
            response = requests.get(
                f"{self.server_url}/api/tasks/statistics",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                stats = response.json()['data']
                self.log_result("✅ 获取任务统计成功", True)
                print(f"   📈 统计信息: {json.dumps(stats, indent=2)}")
            else:
                self.log_result(f"❌ 获取任务统计失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 任务统计异常: {e}", False)
    
    def test_nodes_api(self):
        """测试节点API"""
        print("\n🖥️ 测试节点API...")
        
        try:
            response = requests.get(
                f"{self.server_url}/api/nodes",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                nodes = response.json()['data']
                self.log_result(f"✅ 获取节点列表成功，共 {len(nodes)} 个节点", True)
                
                online_nodes = [n for n in nodes if n['status'] == 'online']
                self.log_result(f"🟢 在线节点: {len(online_nodes)} 个", True)
                
            else:
                self.log_result(f"❌ 获取节点列表失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 节点API测试异常: {e}", False)
    
    def test_storages_api(self):
        """测试存储API"""
        print("\n💾 测试存储API...")
        
        try:
            response = requests.get(
                f"{self.server_url}/api/storages",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                storages = response.json()['data']
                self.log_result(f"✅ 获取存储列表成功，共 {len(storages)} 个存储", True)
                
                storage_types = {}
                for storage in storages:
                    storage_type = storage.get('type', 'unknown')
                    storage_types[storage_type] = storage_types.get(storage_type, 0) + 1
                
                for storage_type, count in storage_types.items():
                    print(f"   📁 {storage_type.upper()}: {count} 个")
                
            else:
                self.log_result(f"❌ 获取存储列表失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 存储API测试异常: {e}", False)
    
    def test_agent_apis(self):
        """测试Agent API端点（不需要认证）"""
        print("\n🤖 测试Agent API...")
        
        # 测试节点注册（不需要token）
        node_info = {
            "name": "test-node",
            "hostname": "test-host",
            "ipaddress": "192.168.1.100",
            "platform": "Linux",
            "python_version": "3.9.0",
            "machine": "x86_64",
            "processor": "Intel",
            "version": "1.0.0"
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/agent/register",
                json=node_info
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("✅ Agent注册测试成功", True)
                print(f"   🆔 返回数据: {json.dumps(data['data'], indent=2)}")
            else:
                self.log_result(f"❌ Agent注册测试失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ Agent API测试异常: {e}", False)
            
    def test_notification_apis(self):
        """测试通知功能API"""
        print("\n📢 测试通知功能API...")
        
        # 1. 测试获取通知设置
        try:
            response = requests.get(
                f"{self.server_url}/api/notifications/settings",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("✅ 获取通知设置成功", True)
            else:
                self.log_result(f"❌ 获取通知设置失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 通知设置API异常: {e}", False)
            
        # 2. 测试获取通知配置
        try:
            response = requests.get(
                f"{self.server_url}/api/notifications/config",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("✅ 获取通知配置成功", True)
            else:
                self.log_result(f"❌ 获取通知配置失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 通知配置API异常: {e}", False)
            
        # 3. 测试获取通知列表
        try:
            response = requests.get(
                f"{self.server_url}/api/notifications/list",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_result("✅ 获取通知列表成功", True)
            else:
                self.log_result(f"❌ 获取通知列表失败: {response.status_code}", False)
                
        except Exception as e:
            self.log_result(f"❌ 通知列表API异常: {e}", False)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 EasySync 系统测试...")
        print("=" * 60)
        
        start_time = time.time()
        
        # 登录
        if not self.login():
            print("❌ 无法登录，跳过需要认证的测试")
            return
        
        # 运行各项测试
        self.test_nodes_api()
        self.test_storages_api()
        self.test_task_statistics()
        self.test_task_crud()
        self.test_connection_test()
        self.test_agent_apis()
        self.test_notification_apis()
        
        # 测试结果汇总
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📋 测试结果汇总:")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            print(f"  {result['message']}")
        
        print(f"\n📊 测试统计:")
        print(f"   ✅ 通过: {passed}/{total}")
        print(f"   ❌ 失败: {total - passed}/{total}")
        print(f"   ⏱️  耗时: {duration:.2f} 秒")
        
        if passed == total:
            print("\n🎉 所有测试通过！系统运行正常！")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败，请检查系统配置")
    
    def log_result(self, message, success):
        """记录测试结果"""
        self.test_results.append({
            'message': message,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })
        print(f"  {message}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='EasySync 系统测试工具')
    parser.add_argument('--server', default='http://localhost:5000', help='服务器地址')
    parser.add_argument('--username', default='admin', help='用户名')
    parser.add_argument('--password', default='admin', help='密码')
    
    args = parser.parse_args()
    
    tester = EasySyncTester(args.server, args.username, args.password)
    tester.run_all_tests()

if __name__ == '__main__':
    main()