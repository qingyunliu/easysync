import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app, Response
from backend.app.auth.services import AuthService
from backend.app.events.service import EventService
from backend.app.models.event import Event
from backend.app.models.alert import AlertPolicy, AlertInstance
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend import db
from backend.app.utils.decorators import handle_errors
from . import events_bp
import csv
import io

logger = logging.getLogger(__name__)

# 事件服务实例
event_service = EventService()

@events_bp.route('', methods=['GET'])
@jwt_required()
@handle_errors
def get_events():
    """获取事件列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    event_type = request.args.get('event_type', '')
    event_action = request.args.get('event_action', '')
    event_result = request.args.get('event_result', '')
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    
    # 转换时间字符串
    start_datetime = None
    end_datetime = None
    
    if start_time:
        try:
            start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except:
            start_datetime = None
    
    if end_time:
        try:
            end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except:
            end_datetime = None
    
    events = event_service.get_events(
        user_id=user_id,
        event_type=event_type if event_type else None,
        event_action=event_action if event_action else None,
        event_result=event_result if event_result else None,
        start_time=start_datetime,
        end_time=end_datetime,
        page=page,
        per_page=per_page
    )
    events["status"] = "success"
    return jsonify(events)


@events_bp.route('/statistics', methods=['GET'])
@jwt_required()
@handle_errors
def get_event_statistics():
    """获取事件统计信息"""
    user_id = get_jwt_identity()
    time_range = request.args.get('time_range', '24h')
    
    stats = event_service.get_event_statistics(user_id, time_range)
    stats["status"] = "success"
    return jsonify(stats)


@events_bp.route('/create', methods=['POST'])
@jwt_required()
@handle_errors
def create_event():
    """创建事件"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event = event_service.create_event(
        user_id=user_id,
        event_type=data['event_type'],
        event_action=data['event_action'],
        event_result=data['event_result'],
        message=data.get('message'),
        details=data.get('details'),
        client_id=data.get('client_id'),
        node_id=data.get('node_id')
    )
    
    return jsonify({
        'message': '事件创建成功',
        'event': event.to_dict()
    })


@events_bp.route('/user', methods=['POST'])
@jwt_required()
@handle_errors
def create_user_event():
    """创建用户事件"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event = event_service.create_user_event(
        user_id=user_id,
        event_action=data['event_action'],
        event_result=data['event_result'],
        message=data.get('message'),
        details=data.get('details')
    )
    
    return jsonify({
        'message': '用户事件创建成功',
        'event': event.to_dict()
    })


@events_bp.route('/storage', methods=['POST'])
@jwt_required()
@handle_errors
def create_storage_event():
    """创建存储事件"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event = event_service.create_storage_event(
        user_id=user_id,
        event_action=data['event_action'],
        event_result=data['event_result'],
        message=data.get('message'),
        details=data.get('details'),
        client_id=data.get('client_id'),
        node_id=data.get('node_id')
    )
    
    return jsonify({
        'message': '存储事件创建成功',
        'event': event.to_dict()
    })


@events_bp.route('/agent', methods=['POST'])
@jwt_required()
@handle_errors
def create_agent_event():
    """创建代理事件"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event = event_service.create_agent_event(
        user_id=user_id,
        event_action=data['event_action'],
        event_result=data['event_result'],
        message=data.get('message'),
        details=data.get('details'),
        node_id=data.get('node_id')
    )
    
    return jsonify({
        'message': '代理事件创建成功',
        'event': event.to_dict()
    })


@events_bp.route('/client', methods=['POST'])
@jwt_required()
@handle_errors
def create_client_event():
    """创建客户端事件"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event = event_service.create_client_event(
        user_id=user_id,
        event_action=data['event_action'],
        event_result=data['event_result'],
        message=data.get('message'),
        details=data.get('details'),
        client_id=data.get('client_id')
    )
    
    return jsonify({
        'message': '客户端事件创建成功',
        'event': event.to_dict()
    })


@events_bp.route('/task', methods=['POST'])
@jwt_required()
@handle_errors
def create_task_event():
    """创建任务事件"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event = event_service.create_task_event(
        user_id=user_id,
        event_action=data['event_action'],
        event_result=data['event_result'],
        message=data.get('message'),
        details=data.get('details'),
        client_id=data.get('client_id'),
        node_id=data.get('node_id')
    )
    
    return jsonify({
        'message': '任务事件创建成功',
        'event': event.to_dict()
    })


@events_bp.route('/system', methods=['POST'])
@jwt_required()
@handle_errors
def create_system_event():
    """创建系统事件"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event = event_service.create_system_event(
        user_id=user_id,
        event_action=data['event_action'],
        event_result=data['event_result'],
        message=data.get('message'),
        details=data.get('details')
    )
    
    return jsonify({
        'message': '系统事件创建成功',
        'event': event.to_dict()
    })


@events_bp.route('/alert-statistics', methods=['GET'])
@jwt_required()
def get_event_alert_statistics():
    """获取事件告警统计信息"""
    try:
        user_id = get_jwt_identity()
        days = int(request.args.get('days', 7))
        
        # 获取事件告警统计
        statistics = event_service.get_event_alert_statistics(user_id, days)
        
        return jsonify({
            'status': 'success',
            'data': statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting event alert statistics: {e}")
        return jsonify({'status': 'error', 'message': f'获取事件告警统计失败: {str(e)}'}), 500


@events_bp.route('/<string:event_id>', methods=['GET'])
@jwt_required()
def get_event_detail(event_id):
    """获取事件详情"""
    try:
        user_id = get_jwt_identity()
        
        # 获取事件详情
        event = Event.query.filter(
            Event.id == event_id,
            Event.user_id == user_id
        ).first()
        
        if not event:
            return jsonify({'status': 'error', 'message': '事件不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'data': event.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting event detail: {e}")
        return jsonify({'status': 'error', 'message': f'获取事件详情失败: {str(e)}'}), 500


@events_bp.route('/types', methods=['GET'])
@jwt_required()
def get_event_types():
    """获取事件类型列表"""
    try:
        user_id = get_jwt_identity()
        
        # 获取所有事件类型
        event_types = db.session.query(Event.event_type).filter(
            Event.user_id == user_id
        ).distinct().all()
        
        types = [event_type[0] for event_type in event_types]
        
        return jsonify({
            'status': 'success',
            'data': types
        })
        
    except Exception as e:
        logger.error(f"Error getting event types: {e}")
        return jsonify({'status': 'error', 'message': f'获取事件类型失败: {str(e)}'}), 500


@events_bp.route('/actions', methods=['GET'])
@jwt_required()
def get_event_actions():
    """获取事件动作列表"""
    try:
        user_id = get_jwt_identity()
        event_type = request.args.get('event_type')
        
        query = db.session.query(Event.event_action).filter(Event.user_id == user_id)
        
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        event_actions = query.distinct().all()
        actions = [action[0] for action in event_actions]
        
        return jsonify({
            'status': 'success',
            'data': actions
        })
        
    except Exception as e:
        logger.error(f"Error getting event actions: {e}")
        return jsonify({'status': 'error', 'message': f'获取事件动作失败: {str(e)}'}), 500


@events_bp.route('/results', methods=['GET'])
@jwt_required()
def get_event_results():
    """获取事件结果列表"""
    try:
        user_id = get_jwt_identity()
        
        # 获取所有事件结果
        event_results = db.session.query(Event.event_result).filter(
            Event.user_id == user_id
        ).distinct().all()
        
        results = [result[0] for result in event_results]
        
        return jsonify({
            'status': 'success',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error getting event results: {e}")
        return jsonify({'status': 'error', 'message': f'获取事件结果失败: {str(e)}'}), 500


@events_bp.route('/cleanup', methods=['POST'])
@jwt_required()
def cleanup_old_events():
    """清理旧事件"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        days = data.get('days', 30)
        
        # 计算清理时间
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 删除旧事件
        deleted_count = Event.query.filter(
            Event.user_id == user_id,
            Event.timestamp < cutoff_date
        ).delete()
        
        db.session.commit()
        
        logger.info(f"Cleaned up {deleted_count} old events for user {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': f'成功清理 {deleted_count} 条旧事件记录',
            'data': {'deleted_count': deleted_count}
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up old events: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'清理旧事件失败: {str(e)}'}), 500


@events_bp.route('/export', methods=['GET'])
@jwt_required()
def export_events():
    """导出事件数据"""
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        event_type = request.args.get('event_type')
        event_action = request.args.get('event_action')
        event_result = request.args.get('event_result')
        
        # 时间范围参数
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        
        start_time = None
        end_time = None
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'status': 'error', 'message': '开始时间格式错误'}), 400
        
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'status': 'error', 'message': '结束时间格式错误'}), 400
        
        # 构建查询
        query = Event.query.filter(Event.user_id == user_id)
        
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if event_action:
            query = query.filter(Event.event_action == event_action)
        if event_result:
            query = query.filter(Event.event_result == event_result)
        if start_time:
            query = query.filter(Event.timestamp >= start_time)
        if end_time:
            query = query.filter(Event.timestamp <= end_time)
        
        # 获取所有匹配的事件
        events = query.order_by(Event.timestamp.desc()).all()
        
        # 转换为CSV格式
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            'ID', '用户ID', '客户端ID', '节点ID', '事件类型', '事件动作', 
            '事件结果', '消息', '详情', '时间戳', '创建时间', '更新时间'
        ])
        
        # 写入数据
        for event in events:
            writer.writerow([
                event.id,
                event.user_id,
                event.client_id or '',
                event.node_id or '',
                event.event_type,
                event.event_action,
                event.event_result,
                event.message or '',
                str(event.details) if event.details else '',
                event.timestamp.isoformat(),
                event.created_at.isoformat() if event.created_at else '',
                event.updated_at.isoformat() if event.updated_at else ''
            ])
        
        # 设置响应头
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=events_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting events: {e}")
        return jsonify({'status': 'error', 'message': f'导出事件数据失败: {str(e)}'}), 500 