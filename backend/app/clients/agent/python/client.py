import os
import sys
import socketio
import threading
import time
import psutil
from datetime import datetime
from typing import Dict, Any


# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from modules.heartbeat import HeartbeatManager
from modules.monitor import MonitorManager
from modules.task import TaskManager
from modules.config import ConfigManager
from modules.logger import LogManager
from modules.upgrade import UpgradeManager

class AgentClient:
    def __init__(self, config_path: str):
        """初始化客户端"""
        # 初始化配置管理器
        self.config_manager = ConfigManager(config_path)
        self.config_manager.start()
        self.config_manager.reload()  # 立即加载配置
        
        # 获取配置
        config = self.config_manager.get_all()
        if not config:
            raise ValueError("无法加载配置文件")

        # 初始化日志管理器
        self.log_manager = LogManager(
            log_dir=config['log']['directory'],
            log_file=config['log']['filename'],
            level=config['log']['level'],
            max_size=config['log']['max_size'],
            backup_count=config['log']['backup_count']
        )
        self.logger = self.log_manager.get_logger("agent.client")
            
        # 初始化其他组件
        self.client_id = config['client']['id']
        self.user_id = config['client']['user_id']
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1000,
            reconnection_delay_max=5000,
            request_timeout=10,
            http_session=None,
            ssl_verify=False,
            logger=True,
            engineio_logger=True
        )
        
        # 初始化各个管理器
        self.heartbeat_manager = HeartbeatManager(
            self.sio,
            self.user_id,
            self.client_id,
            config['server']['heartbeat_interval']
        )
        
        self.monitor_manager = MonitorManager(
            self.sio,
            self.user_id,
            self.client_id,
            config['monitor']['interval'],
            config['monitor']['metrics']
        )
        
        self.task_manager = TaskManager(
            self.sio,
            self.user_id,
            self.client_id
        )
        
        # 初始化升级管理器
        self.upgrade_manager = UpgradeManager(
            self.sio,
            self.user_id,
            self.client_id,
            config['client']['version'],
            config['upgrade']['url'],
            config['upgrade']['backup_dir']
        )
        
        # 注册配置变更回调
        self.config_manager.register_callback(self._on_config_changed)
        
        self._setup_event_handlers()
        
        self.logger.info("客户端初始化完成")
        
    def _on_config_changed(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """处理配置变更"""
        try:
            # 检查服务器配置变更
            if old_config.get('server') != new_config.get('server'):
                self.logger.info("服务器配置已更新，准备重新连接")
                self._reconnect()
                
            # 检查心跳间隔变更
            if old_config.get('server', {}).get('heartbeat_interval') != \
               new_config.get('server', {}).get('heartbeat_interval'):
                self.logger.info(f"心跳间隔已更新: {new_config['server']['heartbeat_interval']}")
                self.heartbeat_manager.interval = new_config['server']['heartbeat_interval']
                
            # 检查监控配置变更
            if old_config.get('monitor') != new_config.get('monitor'):
                self.logger.info("监控配置已更新")
                self.monitor_manager.interval = new_config['monitor']['interval']
                self.monitor_manager.metrics = new_config['monitor']['metrics']
                
            # 检查日志配置变更
            if old_config.get('log') != new_config.get('log'):
                self.logger.info("日志配置已更新")
                self._update_log_config(new_config['log'])
                
            # 检查升级配置变更
            if old_config.get('upgrade') != new_config.get('upgrade'):
                self.logger.info("升级配置已更新")
                self.upgrade_manager.upgrade_url = new_config['upgrade']['url']
                self.upgrade_manager.backup_dir = new_config['upgrade']['backup_dir']
                
        except Exception as e:
            self.logger.error(f"处理配置变更失败: {e}")
            
    def _update_log_config(self, log_config: Dict[str, Any]):
        """更新日志配置"""
        try:
            # 更新日志级别
            if 'level' in log_config:
                self.log_manager.set_level(log_config['level'])
                self.logger.info(f"日志级别已更新: {log_config['level']}")
                
            # 更新日志文件配置
            if 'file' in log_config:
                self.log_manager.add_file_handler(
                    "agent.client",
                    log_config['file']
                )
                self.logger.info(f"日志文件已更新: {log_config['file']}")
                
        except Exception as e:
            self.logger.error(f"更新日志配置失败: {e}")
            
    def _check_health(self) -> bool:
        """检查系统健康状态"""
        try:
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"CPU使用率过高: {cpu_percent}%")
                return False
                
            # 检查内存使用率
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.logger.warning(f"内存使用率过高: {memory.percent}%")
                return False
                
            # 检查磁盘空间
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"磁盘空间不足: {disk.percent}%")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
            
    def _report_upgrade_progress(self, status: str, progress: float = None, message: str = None):
        """报告升级进度"""
        try:
            data = {
                'user_id': self.user_id,
                'client_id': self.client_id,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            if progress is not None:
                data['progress'] = progress
            if message is not None:
                data['message'] = message
                
            self.sio.emit('upgrade_progress', data)
        except Exception as e:
            self.logger.error(f"报告升级进度失败: {e}")
            
    def _handle_upgrade(self, data: Dict[str, Any]):
        """处理升级命令"""
        try:
            # 检查系统健康状态
            if not self._check_health():
                self.logger.error("系统状态不健康，暂不进行升级")
                self._report_upgrade_progress('failed', message='系统状态不健康')
                return
                
            # 设置升级超时
            timeout = data.get('timeout', 300)  # 默认5分钟
            start_time = time.time()
            
            # 检查新版本
            self._report_upgrade_progress('checking')
            latest_version = self.upgrade_manager.check_upgrade()
            if not latest_version:
                self.logger.info("当前已是最新版本")
                self._report_upgrade_progress('latest')
                return
                
            # 下载升级包
            self._report_upgrade_progress('downloading', 0.3)
            upgrade_path = self.upgrade_manager.download_upgrade(latest_version['version'])
            if not upgrade_path:
                self.logger.error("下载升级包失败")
                self._report_upgrade_progress('failed', message='下载升级包失败')
                return
                
            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError("升级超时")
                
            # 备份当前版本
            self._report_upgrade_progress('backing_up', 0.5)
            backup_path = self.upgrade_manager.backup_current()
            if not backup_path:
                self.logger.error("备份当前版本失败")
                self._report_upgrade_progress('failed', message='备份当前版本失败')
                return
                
            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError("升级超时")
                
            # 应用升级
            self._report_upgrade_progress('applying', 0.7)
            if not self.upgrade_manager.apply_upgrade(upgrade_path):
                self.logger.error("应用升级失败，准备回滚")
                self._report_upgrade_progress('rolling_back', 0.8)
                if not self.upgrade_manager.rollback(backup_path):
                    self.logger.error("回滚失败")
                    self._report_upgrade_progress('failed', message='回滚失败')
                return
                
            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError("升级超时")
                
            # 重启客户端
            self._report_upgrade_progress('restarting', 1.0)
            self.upgrade_manager.restart()
            
        except TimeoutError as e:
            self.logger.error(f"升级超时: {e}")
            self._report_upgrade_progress('failed', message='升级超时')
        except Exception as e:
            self.logger.error(f"处理升级失败: {e}")
            self._report_upgrade_progress('failed', message=str(e))
            
    def _setup_event_handlers(self):
        """设置Socket.IO事件处理器"""
        @self.sio.event
        def connect():
            self.logger.info("已连接到服务器")
            # 发送客户端注册信息
            self.sio.emit('register', {
                'user_id': self.user_id,
                'client_id': self.client_id,
                'type': 'agent',
                'capabilities': ['command', 'file_sync'],
                'version': self.config_manager['client']['version'],
                'timestamp': datetime.now().isoformat()
            })
            
            # 加入默认的房间
            self.logger.info(f"加入客户端的房间: client_{self.client_id}")
            self.sio.emit('join', {
                'user_id': self.user_id,
                'client_id': self.client_id,
                'room': f'client_{self.client_id}',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.sio.event
        def disconnect():
            self.logger.info("与服务器断开连接")
            # 停止所有管理器
            self._stop_services()
            # 尝试重连
            if not self._reconnect():
                self.logger.error("重连失败，程序将退出")
                sys.exit(1)
            
        @self.sio.event
        def connect_error(data):
            self.logger.error(f"连接错误: {data}")
            # 禁用 Socket.IO 的自动重连
            self.sio.eio.reconnection = False
            
        @self.sio.event
        def task(data):
            """接收新任务"""
            self.logger.info(f"收到新任务: {data}")
            self.task_manager.execute_task(data)
            
        @self.sio.event
        def upgrade(data):
            """接收升级命令"""
            self.logger.info(f"收到升级命令: {data}")
            self._handle_upgrade(data)
            
        @self.sio.event
        def error(data):
            self.logger.error(f"发生错误: {data}")
            # 如果是服务器端错误导致连接断开，尝试重连
            if data.get('message') == '处理监控数据失败':
                self.logger.info("检测到服务器端错误，准备重连...")
                if not self._reconnect():
                    self.logger.error("重连失败，程序将退出")
                    sys.exit(1)
            
    def _start_services(self):
        """启动所有服务"""
        self.logger.info("正在启动所有服务...")
        
        # 确保 Socket.IO 已连接
        if not self.sio.connected:
            self.logger.error("Socket.IO 未连接，无法启动服务")
            return False
            
        # 停止现有服务
        self._stop_services()
        
        # 定义需要启动的服务列表
        services = [
            (self.heartbeat_manager.start, "心跳服务"),
            (self.monitor_manager.start, "监控服务"),
            (self.task_manager.start, "任务服务")
        ]
        
        self.service_threads = []
        for service_func, service_name in services:
            try:
                thread = threading.Thread(target=service_func)
                thread.daemon = True
                thread.start()
                self.service_threads.append(thread)
                self.logger.info(f"{service_name}已启动")
            except Exception as e:
                self.logger.error(f"启动{service_name}时发生错误: {e}")
                # 如果启动失败，停止所有已启动的服务
                self._stop_services()
                return False
                
        return True
            
    def _stop_services(self):
        """停止所有服务"""
        self.logger.info("正在停止所有服务...")
        
        # 定义需要停止的服务列表
        services = [
            (self.heartbeat_manager, "心跳服务"),
            (self.monitor_manager, "监控服务"),
            (self.task_manager, "任务服务")
        ]
        
        # 遍历服务列表并尝试停止
        for service, name in services:
            try:
                if hasattr(service, 'stop'):
                    service.stop()
                    self.logger.info(f"{name}已停止")
                else:
                    self.logger.warning(f"{name}没有stop方法，跳过停止操作")
            except Exception as e:
                self.logger.error(f"停止{name}时发生错误: {e}")
                
        self.logger.info("所有服务已停止")
            
    def _reconnect(self, max_retries: int = 5, retry_interval: int = 30):
        """重新连接服务器
        
        Args:
            max_retries (int): 最大重试次数，默认5次
            retry_interval (int): 每次重试的间隔时间（秒），默认30秒
        """
        retries = 0
        while retries < max_retries:
            try:
                if self.sio.connected:
                    self.logger.info("正在断开现有连接...")
                    self.sio.disconnect()
                    
                server_url = self.config_manager['server']['url']
                ws_path = self.config_manager['server']['ws_path']
                
                self.logger.info(f"正在进行第 {retries + 1} 次重连尝试，连接到服务器: {server_url}{ws_path}")
                
                # 重新初始化 Socket.IO 客户端
                self.sio = socketio.Client(
                    reconnection=False,  # 禁用自动重连
                    reconnection_attempts=0,
                    reconnection_delay=0,
                    reconnection_delay_max=0,
                    request_timeout=10,
                    http_session=None,
                    ssl_verify=False,
                    logger=True,
                    engineio_logger=True
                )
                
                # 重新设置事件处理器
                self._setup_event_handlers()
                
                # 尝试连接
                self.sio.connect(
                    server_url,
                    socketio_path=ws_path,
                    headers={'Authorization': f'Bearer {self.client_id}'},
                    transports=['websocket'],
                    wait_timeout=10
                )
                
                # 等待连接完全建立
                time.sleep(1)
                
                if not self.sio.connected:
                    raise ConnectionError("Socket.IO 连接未建立")
                    
                self.logger.info("重新连接成功")
                
                # 重新启动所有服务
                if not self._start_services():
                    raise RuntimeError("服务启动失败")
                    
                return True
            except Exception as e:
                retries += 1
                self.logger.error(f"第 {retries} 次重新连接服务器失败: {e}")
                if retries < max_retries:
                    self.logger.info(f"等待 {retry_interval} 秒后进行下一次重试...")
                    time.sleep(retry_interval)
                else:
                    self.logger.error(f"已达到最大重试次数 {max_retries}，放弃重连")
                    return False
                    
    def connect(self):
        """连接到服务器"""
        try:
            server_url = self.config_manager['server']['url']
            ws_path = self.config_manager['server']['ws_path']
            self.logger.info(f"正在连接到服务器: {server_url}{ws_path}")
            
            # 连接到服务器
            self.sio.connect(
                server_url,
                socketio_path=ws_path,
                headers={'Authorization': f'Bearer {self.client_id}'},
                transports=['websocket'],
                wait_timeout=10
            )
            
            self.logger.info("已连接到服务器")
            return True
        except Exception as e:
            self.logger.error(f"连接服务器失败: {e}")
            # 如果连接失败，尝试重连
            return self._reconnect()
            
    def start(self):
        """启动客户端"""
        self.logger.info("正在启动客户端...")
        
        self.connect()
        self._start_services()
        
        try:
            self.sio.wait()
        except KeyboardInterrupt:
            self.logger.info("正在关闭客户端...")
            self._stop_services()
            self.config_manager.stop()
            self.sio.disconnect()
            self.logger.info("客户端已关闭")
            
if __name__ == "__main__":
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "agent/config.yaml"
    )
    client = AgentClient(config_path)
    client.start() 