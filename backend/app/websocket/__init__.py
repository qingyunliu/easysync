from flask import current_app
import logging
from threading import Thread
import time
from datetime import datetime, timedelta
from backend.app.models import Client
from backend import db

# 导入全局 SocketIO 实例
from backend import socketio

# 导出 socketio 实例
__all__ = ['socketio']

logger = logging.getLogger(__name__)

def check_heartbeat_timeout(app):
    """检查心跳超时"""
    while True:
        with app.app_context():
            try:
                # 计算超时阈值（5分钟前的时间点）
                timeout_threshold = datetime.utcnow() - timedelta(minutes=5)
                logger.info(f"Checking clients with last_seen before: {timeout_threshold}")
                
                # 查找超时的客户端（最后一次在线时间早于超时阈值的客户端）
                offline_clients = Client.query.filter(
                    Client.last_seen <= timeout_threshold,
                    Client.agent_status == 'running'
                ).all()
                
                # 打印调试信息
                for client in offline_clients:
                    logger.warning(
                        f"Client {client.name} (ID: {client.id}) timeout detected. "
                        f"Last seen: {client.last_seen}, "
                        f"Threshold: {timeout_threshold}"
                    )
                    client.agent_status = 'offline'
                
                if offline_clients:
                    db.session.commit()
                    
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"Error in offline detection: {str(e)}")
                time.sleep(60)  # 发生错误时也等待一分钟

def init_websocket(app):
    """初始化WebSocket"""
    # 配置SocketIO
    socketio.init_app(
        app,
        cors_allowed_origins="*",  # 允许所有来源的连接
        async_mode='threading',    # 使用线程模式
        path='/ws/socket.io',     # 与客户端匹配的路径
        logger=True,              # 启用日志
        engineio_logger=True,     # 启用 Engine.IO 日志
        ping_timeout=60,          # 增加 ping 超时时间
        ping_interval=25,         # 增加 ping 间隔
        max_http_buffer_size=1e8, # 增加缓冲区大小
        websocket=True,           # 启用 WebSocket
        allow_upgrades=True,      # 允许传输升级
        http_compression=True,    # 启用 HTTP 压缩
        manage_session=False      # 禁用会话管理
    )
    
    # 导入WebSocket事件处理模块
    from . import events
    from . import monitor
    
    # 启动心跳超时检查线程
    heartbeat_checker = Thread(target=check_heartbeat_timeout, args=(app,), daemon=True)
    heartbeat_checker.start()
    
    # 打印初始化信息
    logger.info('WebSocket server initialized')