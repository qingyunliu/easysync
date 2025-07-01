from backend import socketio
from backend.app.models import MonitorData
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def broadcast_monitor_data(client_id, data):
    """广播监控数据到指定客户端的房间"""
    room = f'client_{client_id}'
    #socketio.emit('monitor_update', data, room=room)
    logger.debug(f'Broadcasting monitor data to room {room}')

# 用于存储最后一次数据采集时间
last_collection = {}

def collect_and_broadcast_monitor_data(client_id):
    """采集并广播监控数据"""
    # 检查是否需要采集数据（每5秒采集一次）
    now = datetime.utcnow()
    if client_id in last_collection and (now - last_collection[client_id]).total_seconds() < 5:
        return
    
    last_collection[client_id] = now

    # TODO: 从agent获取数据,主动模式的实现
    
    try:
        
        monitor_data = {}
        # 创建监控数据记录
        MonitorData.create_monitor_data(client_id, monitor_data)

        # 广播数据
        broadcast_monitor_data(client_id, monitor_data)
        
    except Exception as e:
        logger.error(f"Error collecting monitor data: {str(e)}")

def get_historical_data(client_id, start_time, end_time):
    """获取历史监控数据"""
    try:
        query = MonitorData.query.filter(
            MonitorData.client_id == client_id,
            MonitorData.timestamp.between(start_time, end_time)
        ).order_by(MonitorData.timestamp.asc())
        
        return [item.to_dict() for item in query.all()]
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return [] 