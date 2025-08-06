#!/usr/bin/env python3
"""
EasySync Proxy 任务执行器
处理来自服务器的同步任务，支持多种存储类型
"""

import os
import json
import time
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Tuple, List
import requests
import logging
from datetime import datetime
from .services.mount_manager import get_mount_manager
from .utils.logger import get_log_manager

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, server_url: str, auth_token: str, node_id: str):
        self.server_url = server_url
        self.auth_token = auth_token
        self.node_id = node_id
        self.log_manager = get_log_manager()
        self.logger = self.log_manager.get_logger('TaskExecutor')
        self.active_mounts = []  # 跟踪活动挂载点
        self.running_tasks = set()  # 跟踪正在运行的任务ID
        self.last_heartbeat = 0  # 上次心跳时间
    
    def send_heartbeat(self) -> bool:
        """发送心跳"""
        try:
            import psutil
            
            payload = {
                'system_info': {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'load_average': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
                    'active_tasks': len(self.running_tasks),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                f"{self.server_url}/api/agent/{self.node_id}/heartbeat",
                json=payload,
                headers={'Authorization': f'Bearer {self.auth_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.last_heartbeat = time.time()
                return True
            else:
                self.logger.error(f"心跳发送失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"心跳发送异常: {e}")
            return False
        
    def fetch_tasks(self) -> List[Dict[str, Any]]:
        """从服务器获取任务"""
        try:
            response = requests.get(
                f"{self.server_url}/api/agent/{self.node_id}/tasks",
                headers={'Authorization': f'Bearer {self.auth_token}'}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                self.logger.error(f"获取任务失败: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取任务异常: {e}")
            return []
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """执行任务"""
        task_id = task['id']
        
        # 避免重复执行同一任务
        if task_id in self.running_tasks:
            self.logger.info(f"任务 {task_id} 已在运行中，跳过")
            return True
        
        # 如果任务已经在运行状态，不重复执行
        if task.get('status') == 'running':
            self.logger.info(f"任务 {task_id} 已在运行状态，跳过")
            return True
        
        self.logger.info(f"开始执行任务: {task_id}")
        self.running_tasks.add(task_id)
        
        try:
            # 更新任务状态为运行中
            self.update_task_status(task_id, 'running', 0)
            
            # 根据源端类型选择执行方式
            if task['source_type'] == 'storage':
                result = self.execute_storage_task(task)
            elif task['source_type'] == 'client':
                result = self.execute_client_task(task)
            else:
                raise ValueError(f"不支持的源端类型: {task['source_type']}")
            
            return result
                
        except Exception as e:
            self.logger.error(f"任务执行失败: {e}")
            self.update_task_status(task_id, 'failed', error=str(e))
            return False
        finally:
            # 清理资源
            self.cleanup_resources()
            # 从运行中任务集合移除
            self.running_tasks.discard(task_id)
    
    def execute_storage_task(self, task: Dict[str, Any]) -> bool:
        """执行存储到存储的同步任务"""
        task_id = task['id']
        source_config = task.get('source_storage_config')
        target_config = task.get('target_storage_config')
        
        if not source_config or not target_config:
            raise ValueError("缺少存储配置信息")
        
        # 报告进度：准备阶段
        self.report_progress(task_id, 10, "准备存储连接")
        
        # 处理源端存储
        source_path = self.prepare_storage(source_config, task['source_path'])
        self.report_progress(task_id, 30, f"源端存储准备完成: {source_path}")
        
        # 处理目标端存储  
        target_path = self.prepare_storage(target_config, task['target_path'])
        self.report_progress(task_id, 50, f"目标端存储准备完成: {target_path}")
        
        # 执行同步
        self.report_progress(task_id, 60, "开始数据同步")
        sync_result = self.execute_sync(source_path, target_path, task.get('options', {}))
        
        if sync_result:
            self.update_task_status(task_id, 'completed', 100)
            self.report_progress(task_id, 100, "同步完成")
            return True
        else:
            self.update_task_status(task_id, 'failed', error="同步失败")
            return False
    
    def execute_client_task(self, task: Dict[str, Any]) -> bool:
        """执行客户端任务（转发给客户端）"""
        task_id = task['id']
        client_config = task.get('source_client_config')
        
        if not client_config:
            raise ValueError("缺少客户端配置信息")
        
        # 构建客户端任务
        client_task = {
            'id': task_id,
            'source_path': task['source_path'],
            'target_storage_config': task.get('target_storage_config'),
            'target_path': task['target_path'],
            'options': task.get('options', {})
        }
        
        # 发送任务给客户端（这里需要实现具体的通信方式）
        success = self.send_task_to_client(client_config, client_task)
        
        if success:
            self.update_task_status(task_id, 'assigned')
            self.report_progress(task_id, 10, f"任务已发送给客户端: {client_config['ip_address']}")
            return True
        else:
            self.update_task_status(task_id, 'failed', error="无法连接到客户端")
            return False
    
    def prepare_storage(self, storage_config: Dict[str, Any], task_path: str) -> str:
        """准备存储访问"""
        storage_type = storage_config['type']
        
        if storage_type in ['nas', 'nfs']:
            return self.prepare_nas_storage(storage_config, task_path)
        elif storage_type in ['s3', 'obs']:
            return self.prepare_s3_storage(storage_config, task_path)
        elif storage_type == 'local':
            return self.prepare_local_storage(storage_config, task_path)
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
    
    def prepare_nas_storage(self, storage_config: Dict[str, Any], task_path: str) -> str:
        """准备NAS存储挂载"""
        storage_id = storage_config.get('id', str(time.time()))
        
        try:
            # 使用挂载管理器挂载存储
            mount_manager = get_mount_manager()
            mount_point = mount_manager.mount_storage(storage_id, storage_config)
            
            if not mount_point:
                raise Exception("挂载管理器挂载失败")
            
            # 返回实际的文件路径
            if task_path:
                return os.path.join(mount_point, task_path.lstrip('/'))
            else:
                return mount_point
                
        except Exception as e:
            self.logger.error(f"准备NAS存储失败: {e}")
            raise
    
    def prepare_s3_storage(self, storage_config: Dict[str, Any], task_path: str) -> str:
        """准备S3存储（返回rclone格式路径）"""
        config = storage_config['config']
        
        # 生成rclone remote名称
        remote_name = f"s3_{storage_config['id']}"
        
        # 创建rclone配置文件
        self.create_rclone_config(remote_name, config)
        
        # 返回rclone路径格式
        return f"{remote_name}:{task_path}"
    
    def prepare_local_storage(self, storage_config: Dict[str, Any], task_path: str) -> str:
        """准备本地存储"""
        config = storage_config['config']
        base_path = config.get('base_path', '/data')
        
        # 组合完整路径
        full_path = os.path.join(base_path, task_path.lstrip('/'))
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        return full_path
    
    def create_rclone_config(self, remote_name: str, s3_config: Dict[str, Any]):
        """创建rclone配置"""
        config_dir = os.path.expanduser('~/.config/rclone')
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, 'rclone.conf')
        
        # 读取现有配置
        config_content = ""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_content = f.read()
        
        # 添加新的remote配置
        new_config = f"""
[{remote_name}]
type = s3
access_key_id = {s3_config['access_key']}
secret_access_key = {s3_config['secret_key']}
region = {s3_config['region']}
"""
        
        if s3_config.get('endpoint'):
            new_config += f"endpoint = {s3_config['endpoint']}\n"
        
        # 如果配置中不存在这个remote，则添加
        if f"[{remote_name}]" not in config_content:
            with open(config_file, 'a') as f:
                f.write(new_config)
    
    def execute_sync(self, source_path: str, target_path: str, options: Dict[str, Any]) -> bool:
        """执行数据同步"""
        try:
            # 判断是否使用rclone（当路径包含:时）
            if ':' in source_path or ':' in target_path:
                return self.execute_rclone_sync(source_path, target_path, options)
            else:
                return self.execute_rsync(source_path, target_path, options)
                
        except Exception as e:
            self.logger.error(f"同步执行失败: {e}")
            return False
    
    def execute_rclone_sync(self, source_path: str, target_path: str, options: Dict[str, Any]) -> bool:
        """使用rclone执行同步"""
        cmd = ['rclone', 'sync', source_path, target_path]
        
        # 添加选项
        if options.get('delete', False):
            cmd.append('--delete-during')
        
        if options.get('checksum', True):
            cmd.append('--checksum')
        
        if options.get('compress', False):
            cmd.append('--compress')
        
        if options.get('bandwidth_limit', 0) > 0:
            cmd.extend(['--bwlimit', f"{options['bandwidth_limit']}M"])
        
        # 添加进度显示
        cmd.extend(['--progress', '--stats', '10s'])
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.logger.info("rclone同步成功")
            return True
        else:
            self.logger.error(f"rclone同步失败: {result.stderr}")
            return False
    
    def execute_rsync(self, source_path: str, target_path: str, options: Dict[str, Any]) -> bool:
        """使用rsync执行同步"""
        cmd = ['rsync', '-avz']
        
        # 添加选项
        if options.get('delete', False):
            cmd.append('--delete')
        
        if options.get('checksum', True):
            cmd.append('--checksum')
        
        if not options.get('compress', False):
            cmd.append('--no-compress')
        
        if options.get('bandwidth_limit', 0) > 0:
            cmd.append(f"--bwlimit={options['bandwidth_limit']}000")
        
        # 添加源和目标
        cmd.extend([source_path, target_path])
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.logger.info("rsync同步成功")
            return True
        else:
            self.logger.error(f"rsync同步失败: {result.stderr}")
            return False
    
    def send_task_to_client(self, client_config: Dict[str, Any], task: Dict[str, Any]) -> bool:
        """发送任务给客户端"""
        # 这里需要实现与客户端的通信逻辑
        # 可以使用WebSocket、HTTP或其他方式
        self.logger.info(f"发送任务给客户端: {client_config['ip_address']}")
        return True
    
    def update_task_status(self, task_id: str, status: str, progress: int = None, error: str = None):
        """更新任务状态"""
        payload = {
            'status': status,
            'progress': progress,
            'error': error
        }
        
        try:
            response = requests.put(
                f"{self.server_url}/api/agent/{self.node_id}/tasks/{task_id}/status",
                json=payload,
                headers={'Authorization': f'Bearer {self.auth_token}'}
            )
            
            if response.status_code != 200:
                self.logger.error(f"更新任务状态失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"更新任务状态异常: {e}")
    
    def report_progress(self, task_id: str, progress: int, message: str, details: Dict[str, Any] = None):
        """上报任务进度"""
        payload = {
            'status': 'progress',
            'message': f"进度 {progress}%: {message}",
            'details': {
                'progress': progress,
                'current_step': message,
                'step_details': details or {}
            }
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/agent/{self.node_id}/tasks/{task_id}/logs",
                json=payload,
                headers={'Authorization': f'Bearer {self.auth_token}'}
            )
            
            if response.status_code != 200:
                self.logger.error(f"上报进度失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"上报进度异常: {e}")
    
    def cleanup_resources(self):
        """清理资源"""
        try:
            # 使用挂载管理器清理废弃的挂载点
            mount_manager = get_mount_manager()
            cleaned_count = mount_manager.cleanup_abandoned_mounts()
            
            if cleaned_count > 0:
                self.logger.info(f"清理了 {cleaned_count} 个废弃挂载点")
            
            # 清理活跃挂载记录（这个列表现在可能不需要了，但为了兼容性保留）
            self.active_mounts.clear()
            
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
    
    def cleanup_storage_mount(self, storage_id: str):
        """清理特定存储的挂载"""
        try:
            mount_manager = get_mount_manager()
            success = mount_manager.unmount_storage(storage_id)
            
            if success:
                self.logger.info(f"成功卸载存储 {storage_id}")
            else:
                self.logger.warning(f"卸载存储 {storage_id} 失败")
                
        except Exception as e:
            self.logger.error(f"清理存储挂载失败: {e}")


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 从环境变量或配置文件读取配置
    server_url = os.getenv('EASYSYNC_SERVER_URL', 'http://localhost:5000')
    auth_token = os.getenv('EASYSYNC_AUTH_TOKEN')
    node_id = os.getenv('EASYSYNC_NODE_ID')
    
    if not auth_token or not node_id:
        logging.error("缺少认证令牌或节点ID")
        return
    
    executor = TaskExecutor(server_url, auth_token, node_id)
    
    # 主循环：获取和执行任务
    while True:
        try:
            # 定期发送心跳（每60秒）
            current_time = time.time()
            if current_time - executor.last_heartbeat > 60:
                executor.send_heartbeat()
            
            tasks = executor.fetch_tasks()
            
            # 过滤出需要执行的任务（assigned状态的新任务）
            new_tasks = [task for task in tasks if task.get('status') == 'assigned']
            
            if new_tasks:
                executor.logger.info(f"发现 {len(new_tasks)} 个新任务")
                for task in new_tasks:
                    executor.execute_task(task)
            
            # 等待一段时间后再次检查任务
            time.sleep(30)
            
        except KeyboardInterrupt:
            logging.info("收到停止信号")
            break
        except Exception as e:
            logging.error(f"主循环异常: {e}")
            time.sleep(60)  # 出错后等待更长时间
        finally:
            executor.cleanup_resources()


if __name__ == '__main__':
    main()