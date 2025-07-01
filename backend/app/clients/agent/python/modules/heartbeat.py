import time
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HeartbeatManager:
    def __init__(self, sio, user_id: str, client_id: str, interval: int = 30):
        self.sio = sio
        self.user_id = user_id
        self.client_id = client_id
        self.interval = interval
        self._running = False
        
    def start(self):
        """启动心跳"""
        self._running = True
        while self._running:
            try:
                self._send_heartbeat()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"发送心跳失败: {e}")
                time.sleep(5)  # 发生错误时等待5秒后重试
                
    def stop(self):
        """停止心跳"""
        self._running = False
        
    def _send_heartbeat(self):
        """发送心跳数据"""
        try:
            heartbeat_data = {
                'user_id': str(self.user_id),
                'client_id': str(self.client_id),
                'timestamp': datetime.now().isoformat(),
                'status': 'alive'
            }
            self.sio.emit('heartbeat', heartbeat_data)
            logger.debug(f"发送心跳: {heartbeat_data}")
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")
            raise 