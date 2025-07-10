import logging
import threading
import time
import platform
import socket
import subprocess
import requests
from datetime import datetime
from .communication import ServerCommunication
from ..services.monitor_service import MonitorService
from ..services.sync_service import SyncService

class CommandService:
    def __init__(self, config, node_id, token, server_url):
        self.config = config
        self.node_id = node_id
        self.token = token
        self.server_url = server_url
        self.running = False
        self.poll_interval = config.get('command_poll_interval', 10)

    def start(self):
        self.running = True
        while self.running:
            try:
                self.poll_and_execute()
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"Command poll error: {e}")
                time.sleep(5)

    def poll_and_execute(self):
        url = f"{self.server_url}/api/agent/v1/nodes/{self.node_id}/commands"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                commands = resp.json().get('data', [])
                for cmd in commands:
                    result = self.execute_command(cmd)
                    self.report_command_result(cmd['id'], result)
        except Exception as e:
            print(f"命令拉取失败: {e}")

    def execute_command(self, cmd):
        if cmd.get('type') == 'shell':
            try:
                completed = subprocess.run(
                    cmd['command'],
                    shell=True,
                    capture_output=True,
                    timeout=cmd.get('timeout', 60),
                    text=True
                )
                return {
                    'return_code': completed.returncode,
                    'stdout': completed.stdout,
                    'stderr': completed.stderr
                }
            except Exception as e:
                return {
                    'return_code': -1,
                    'stdout': '',
                    'stderr': str(e)
                }
        # 可扩展其它类型
        return {'return_code': -2, 'stdout': '', 'stderr': 'Unknown command type'}

    def report_command_result(self, cmd_id, result):
        url = f"{self.server_url}/api/agent/v1/nodes/{self.node_id}/commands/{cmd_id}/result"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            requests.post(url, json={'result': result}, headers=headers, timeout=5)
        except Exception as e:
            print(f"命令结果上报失败: {e}")

class ProxyAgent:
    """代理类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger('ProxyAgent')
        self.server_comm = ServerCommunication(config)
        self.monitor_service = MonitorService(config, None, None)  # node_id/token后续赋值
        self.sync_service = SyncService(config)
        self.running = False
        self.heartbeat_thread = None
        self.task_poll_thread = None
        self.command_thread = None
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        self.task_poll_interval = self.config.get('task_poll_interval', 10)
        self.node_id = None
        self.token = None
        self.version = self.config.get('version', '1.0.0')
        self.start_time = time.time()
        self.command_service = None
        self._setup_services()

    def _setup_services(self):
        self.monitor_service.add_callback(self._on_monitor_update)
        self.sync_service.add_callback(self._on_sync_update)

    def _get_ipaddress(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        self.running = True
        # 注册节点，获取node_id和token
        self._register_node()
        # 更新monitor_service的node_id和token
        self.monitor_service.node_id = self.node_id
        self.monitor_service.token = self.token
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        # 启动监控服务
        threading.Thread(target=self.monitor_service.start, daemon=True).start()
        # 启动任务拉取线程
        self.task_poll_thread = threading.Thread(target=self._task_poll_loop, daemon=True)
        self.task_poll_thread.start()
        # 启动同步服务
        self.sync_service.start()
        # 启动命令服务
        self.command_service = CommandService(self.config, self.node_id, self.token, self.server_comm.server_url)
        self.command_thread = threading.Thread(target=self.command_service.start, daemon=True)
        self.command_thread.start()

    def stop(self):
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        if self.task_poll_thread:
            self.task_poll_thread.join(timeout=5)
        if self.command_thread:
            self.command_thread.join(timeout=5)
        self.monitor_service.stop()
        self.sync_service.stop()

    def _register_node(self):
        node_info = {
            'name': platform.node(),
            'hostname': platform.node(),
            'ipaddress': self._get_ipaddress(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'version': self.version
        }
        node_id = self.server_comm.register_node(node_info)
        if not node_id:
            raise Exception("Failed to register node")
        self.node_id = node_id
        self.token = self.server_comm.token
        self.config['node_id'] = node_id
        self.logger.info(f"Node registered with ID: {node_id}")

    def _heartbeat_loop(self):
        while self.running:
            try:
                uptime = int(time.time() - self.start_time)
                heartbeat_info = {
                    "node_id": self.node_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": self.version,
                    "status": "online",
                    "ipaddress": self._get_ipaddress(),
                    "hostname": platform.node(),
                    "uptime": uptime
                }
                if not self.server_comm.send_heartbeat(heartbeat_info):
                    self.logger.warning("Failed to send heartbeat")
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
            time.sleep(self.heartbeat_interval)

    def _task_poll_loop(self):
        while self.running:
            try:
                tasks = self.server_comm.get_tasks()
                if tasks:
                    for task in tasks:
                        self.sync_service.add_task(task)
            except Exception as e:
                self.logger.error(f"Error in task poll loop: {e}")
            time.sleep(self.task_poll_interval)

    def _on_monitor_update(self, metrics):
        self.logger.debug(f"Monitor update: {metrics}")

    def _on_sync_update(self, status):
        self.logger.debug(f"Sync update: {status}")

    def wait(self):
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def is_healthy(self):
        return self.running and self.heartbeat_thread and self.heartbeat_thread.is_alive() and self.task_poll_thread and self.task_poll_thread.is_alive() and self.command_thread and self.command_thread.is_alive() 