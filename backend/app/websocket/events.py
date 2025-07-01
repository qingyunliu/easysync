from flask_socketio import emit, join_room, leave_room, disconnect
from . import socketio
from backend.app.models import Client, MonitorData
from backend import db
from flask import request
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    try:
        # 获取客户端信息
        client_id = request.args.get('client_id')
        if not client_id and request.environ.get('HTTP_AUTHORIZATION'):
            # 从 Authorization 头中获取 client_id
            auth_header = request.environ['HTTP_AUTHORIZATION']
            if auth_header.startswith('Bearer '):
                client_id = auth_header[7:]
        
        logger.info(f'Client attempting to connect with ID: {client_id}')
        logger.debug(f'Connection headers: {dict(request.headers)}')
        logger.debug(f'Connection args: {dict(request.args)}')
        logger.debug(f'Connection environ: {dict(request.environ)}')
        
        if not client_id:
            logger.warning('Connection attempt without client_id')
            disconnect()
            return False
        
        # 验证客户端
        client = Client.query.get(client_id)
        if not client:
            logger.warning(f'Invalid client_id: {client_id}')
            disconnect()
            return False
        
        # 更新客户端状态
        client.agent_status = 'running'
        client.last_seen = datetime.utcnow()
        db.session.commit()
        
        # 加入默认房间
        join_room(f'client_{client_id}')
        
        logger.info(f'Client {client_id} connected successfully')
        emit('connected', {
            'status': 'success',
            'room': f'client_{client_id}',
            'message': 'Connected to server',
            'client_id': client_id,
            'timestamp': datetime.utcnow().isoformat(),
        })
        return True
        
    except Exception as e:
        logger.error(f'Error in handle_connect: {str(e)}')
        disconnect()
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    try:
        client_id = request.args.get('client_id')
        if client_id:
            client = Client.query.get(client_id)
            if client:
                client.agent_status = 'offline'
                client.last_seen = datetime.utcnow()
                db.session.commit()
                logger.info(f'Client {client_id} disconnected')
    except Exception as e:
        logger.error(f'Error in handle_disconnect: {str(e)}')

@socketio.on('join')
def handle_join(data):
    """客户端加入房间"""
    try:
        user_id = data.get('user_id')
        client_id = data.get('client_id')
        room = data.get('room', f'client_{client_id}')
        
        if client_id:
            join_room(room)
            emit('joined', {
                'room': room,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.info(f'Client {client_id} joined room {room}')
        else:
            logger.warning('Join request without client_id')
            emit('error', {'message': 'Missing client_id'})
    except Exception as e:
        logger.error(f'Error in handle_join: {str(e)}')
        emit('error', {'message': 'Internal server error'})

@socketio.on('heartbeat')
def handle_heartbeat(data):
    """处理心跳消息"""
    try:
        user_id = data.get('user_id')
        client_id = data.get('client_id')
        if not client_id or not user_id:
            logger.warning('Heartbeat without client_id or user_id')
            return
            
        # 更新客户端最后活动时间
        client = Client.query.get(client_id)
        if client:
            client.user_id = user_id
            client.last_seen = datetime.utcnow()
            client.agent_status = 'running'
            db.session.commit()
            
            emit('heartbeat_ack', {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'success'
            })
            logger.debug(f'Received heartbeat from client {client_id}')
        else:
            logger.warning(f'Client {client_id} not found')
            emit('error', {'message': '客户端不存在'})
    except Exception as e:
        logger.error(f'Error in handle_heartbeat: {str(e)}')
        db.session.rollback()

@socketio.on('leave')
def handle_leave(data):
    """客户端离开房间"""
    try:
        client_id = data.get('client_id')
        room = data.get('room', f'client_{client_id}')
        
        if not client_id:
            logger.warning('Leave request without client_id')
            return
            
        leave_room(room)
        client = Client.query.get(client_id)
        if client:
            client.agent_status = 'offline'
            db.session.commit()
            logger.info(f'Client {client_id} left room {room}')
        else:
            logger.warning(f'Client {client_id} not found')
            
    except Exception as e:
        logger.error(f'Error in handle_leave: {str(e)}')
        db.session.rollback()

@socketio.on('metrics')
def handle_monitor_data(data):
    """处理监控数据"""
    try:
        user_id = data.get('user_id')
        client_id = data.get('client_id')
        if not client_id:
            logger.error('Monitor data without client_id')
            return
        
        # 保存监控数据
        logger.info(f'Received metrics data from client {client_id}')
        
        # 创建监控数据记录
        monitor_data = MonitorData.create_monitor_data(user_id=user_id, client_id=client_id, data=data)
        
        # 广播到对应的房间
        room = f'client_{client_id}'
        emit('monitor_update', {
            'user_id': user_id,
            'client_id': client_id,
            'timestamp': datetime.utcnow().isoformat(),
            'data': monitor_data.to_dict()
        }, room=room)
        
        logger.debug(f'Processed and broadcasted monitor data for client {client_id}')
    except Exception as e:
        logger.error(f'Error processing monitor data: {str(e)}')
        emit('error', {'message': '处理监控数据失败'})

@socketio.on('logs')
def handle_logs(data):
    """处理系统日志数据"""
    try:
        user_id = data.get('user_id')
        client_id = data.get('client_id')
        logs = data.get('logs', [])
        
        if not client_id:
            logger.error('Logs data without client_id')
            return
            
        # 验证客户端
        client = Client.query.get(client_id)
        if not client:
            logger.warning(f'Invalid client_id: {client_id}')
            return
            
        # 广播日志到对应的房间
        room = f'client_{client_id}'
        emit('logs_update', {
            'user_id': user_id,
            'client_id': client_id,
            'timestamp': datetime.utcnow().isoformat(),
            'logs': logs
        }, room=room)
        
        logger.debug(f'Processed and broadcasted logs for client {client_id}')
    except Exception as e:
        logger.error(f'Error processing logs: {str(e)}')
        emit('error', {'message': '处理日志数据失败'})

@socketio.on('health_check')
def handle_health_check(data):
    """处理健康检查数据"""
    try:
        user_id = data.get('user_id')
        client_id = data.get('client_id')
        status = data.get('status')
        
        if not client_id or not user_id or not status:
            logger.warning('Health check without client_id, user_id or status')
            return
            
        client = Client.query.get(client_id)
        if client:
            client.last_seen = datetime.utcnow()
            client.agent_status = 'running' if status == 'ok' else 'error'
            db.session.commit()
            logger.info(f'Health check updated for client {client_id}: {status}')
        else:
            logger.warning(f'Client {client_id} not found for health check')
            
    except Exception as e:
        logger.error(f'Error handling health check: {str(e)}')
        db.session.rollback()

@socketio.on('sync_task_result')
def handle_sync_task_result(data):
    """处理同步任务结果"""
    try:
        client_id = data.get('client_id')
        task_id = data.get('task_id')
        status = data.get('status')
        message = data.get('message')
        
        if not all([client_id, task_id, status]):
            logger.warning('Sync task result missing required fields')
            return
            
        # 发送确认消息给客户端
        emit('sync_task_ack', {
            'task_id': task_id,
            'status': 'received',
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'client_{client_id}')
        
        logger.info(f'Sync task {task_id} result received from client {client_id}: {status}')
        
    except Exception as e:
        logger.error(f'Error handling sync task result: {str(e)}')

@socketio.on('subscribe')
def handle_subscribe(data):
    """处理前端订阅请求"""
    try:
        client_id = data.get('client_id')
        if not client_id:
            logger.warning('Subscribe request without client_id')
            return
            
        # 加入对应的房间
        room = f'client_{client_id}'
        join_room(room)
        
        # 发送确认消息
        emit('subscribed', {
            'client_id': client_id,
            'room': room,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f'Client subscribed to room {room}')
    except Exception as e:
        logger.error(f'Error handling subscribe request: {str(e)}')
        emit('error', {'message': '订阅失败'})

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """处理前端取消订阅请求"""
    try:
        client_id = data.get('client_id')
        if not client_id:
            logger.warning('Unsubscribe request without client_id')
            return
            
        # 离开对应的房间
        room = f'client_{client_id}'
        leave_room(room)
        
        # 发送确认消息
        emit('unsubscribed', {
            'client_id': client_id,
            'room': room,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f'Client unsubscribed from room {room}')
    except Exception as e:
        logger.error(f'Error handling unsubscribe request: {str(e)}')
        emit('error', {'message': '取消订阅失败'})
