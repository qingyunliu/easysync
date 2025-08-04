from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models import MonitorData, Client, Node
from datetime import datetime, timedelta
from sqlalchemy import func
from . import monitor_bp
from .service import MonitorService
from .errors import MonitorError, MonitorNotFoundError, MonitorValidationError, MonitorOperationError, AlertRuleError
import logging
from backend.app.auth.services import AuditService
from backend.app.notifications.services import NotificationService
from backend.app.utils.utils import get_system_metrics

logger = logging.getLogger(__name__)

monitor_service = MonitorService()
notification_service = NotificationService()

@monitor_bp.errorhandler(MonitorError)
def handle_monitor_error(error):
    """处理监控错误"""
    if isinstance(error, MonitorNotFoundError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 404
    elif isinstance(error, MonitorValidationError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
    elif isinstance(error, MonitorOperationError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
    elif isinstance(error, AlertRuleError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
    else:
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 500

@monitor_bp.route('/<string:resource_id>/history', methods=['GET'])
@jwt_required()
def get_monitor_history(resource_id):
    """获取历史监控数据"""
    try:
        client = Client.query.filter_by(id=resource_id).first()
        node = Node.query.filter_by(id=resource_id).first()

        # 获取查询参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        interval = request.args.get('interval', '1h')  # 默认1小时
        metrics = request.args.getlist('metrics')  # 要查询的指标
        
        # 构建查询
        if client:
            query = MonitorData.query.filter_by(client_id=client.id)
        elif node:
            query = MonitorData.query.filter_by(node_id=node.id)
        else:
            return jsonify({
                'status': 'error',
                'message': '资源不存在'
            }), 404

        # 时间范围过滤
        if start_time:
            query = query.filter(MonitorData.timestamp >= datetime.fromisoformat(start_time.replace('Z', '+00:00')))
        if end_time:
            query = query.filter(MonitorData.timestamp <= datetime.fromisoformat(end_time.replace('Z', '+00:00')))
        
        # 按时间间隔聚合
        if interval == '1m':
            query = query.order_by(MonitorData.timestamp.desc()).limit(60)
        elif interval == '5m':
            query = query.order_by(MonitorData.timestamp.desc()).limit(12)
        elif interval == '15m':
            query = query.order_by(MonitorData.timestamp.desc()).limit(4)
        elif interval == '1h':
            query = query.order_by(MonitorData.timestamp.desc()).limit(24)
        elif interval == '1d':
            query = query.order_by(MonitorData.timestamp.desc()).limit(30)
        
        # 执行查询
        monitor_data = query.all()
        
        # 处理返回数据
        result = []
        for data in monitor_data:
            data_dict = data.to_dict()
            if metrics:
                filtered_data = {'timestamp': data_dict['timestamp']}
                for metric in metrics:
                    if metric in data_dict:
                        filtered_data[metric] = data_dict[metric]
                result.append(filtered_data)
            else:
                result.append(data_dict)
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"获取历史监控数据失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取历史监控数据失败: {str(e)}'
        }), 500

@monitor_bp.route('/<string:client_id>/stats', methods=['GET'])
def get_monitor_stats(client_id):
    """获取监控统计数据"""
    try:
        # 获取最近24小时的数据
        start_time = datetime.utcnow() - timedelta(hours=24)
        
        # 查询统计数据
        stats = db.session.query(
            func.avg(MonitorData.cpu_usage).label('avg_cpu'),
            func.max(MonitorData.cpu_usage).label('max_cpu'),
            func.avg(MonitorData.memory_usage).label('avg_memory'),
            func.max(MonitorData.memory_usage).label('max_memory'),
            func.sum(MonitorData.network_receive).label('total_receive'),
            func.sum(MonitorData.network_send).label('total_send')
        ).filter(
            MonitorData.client_id == client_id,
            MonitorData.timestamp >= start_time
        ).first()
        
        result = {
            'cpu': {
                'average': round(stats.avg_cpu or 0, 2),
                'maximum': round(stats.max_cpu or 0, 2)
            },
            'memory': {
                'average': round(stats.avg_memory or 0, 2),
                'maximum': round(stats.max_memory or 0, 2)
            },
            'network': {
                'total_receive': stats.total_receive or 0,
                'total_send': stats.total_send or 0
            }
        }
        
        logger.info(f'Retrieved monitor stats for client {client_id}')
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f'Error getting monitor stats: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@monitor_bp.route('/metrics', methods=['POST'])
@jwt_required()
def save_metrics():
    """保存监控指标"""
    data = request.get_json()
    node_id = data.get('node_id')
    metrics = data.get('metrics', {})
    
    try:
        monitor_service.save_metrics(node_id, metrics)
        return jsonify({
            'status': 'success',
            'message': '监控指标保存成功'
        })
    except MonitorValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@monitor_bp.route('/<string:node_id>/stats', methods=['GET'])
@jwt_required()
def get_node_stats(node_id):
    """获取节点统计信息"""
    try:
        stats = monitor_service.get_node_stats(node_id)
        return jsonify({
            'status': 'success',
            'message': '统计信息获取成功',
            'data': stats
        })
    except MonitorNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404

@monitor_bp.route('/<string:node_id>/history', methods=['GET'])
@jwt_required()
def get_node_history(node_id):
    """获取节点历史数据"""
    duration = request.args.get('duration', '24h')
    
    try:
        history = monitor_service.get_node_history(node_id, duration)
        return jsonify({
            'status': 'success',
            'message': '历史数据获取成功',
            'data': history
        })
    except MonitorNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except MonitorValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@monitor_bp.route('/system/status', methods=['GET'])
@jwt_required()
def get_system_status():
    """获取系统监控状态"""
    try:
        metrics = get_system_metrics()
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@monitor_bp.route('/system/metrics', methods=['GET'])
@jwt_required()
def get_system_metrics_history():
    """获取系统监控数据"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取查询参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        interval = request.args.get('interval', '1m')  # 默认1分钟
        limit = request.args.get('limit', 24, type=int)  # 默认24个数据点
        
        # 构建查询 - 获取系统级别的监控数据（node_id为None表示系统级别）
        query = MonitorData.query.filter_by(
            user_id=current_user_id,
            node_id=None,
            client_id=None
        )
        
        # 时间范围过滤
        if start_time:
            query = query.filter(MonitorData.timestamp >= datetime.fromisoformat(start_time.replace('Z', '+00:00')))
        if end_time:
            query = query.filter(MonitorData.timestamp <= datetime.fromisoformat(end_time.replace('Z', '+00:00')))
        
        # 按时间排序并限制数量
        query = query.order_by(MonitorData.timestamp.desc()).limit(limit)
        
        # 执行查询
        monitor_data = query.all()
        
        # 处理返回数据
        result = []
        for data in monitor_data:
            data_dict = data.to_dict()
            if data_dict['data']:
                # 提取系统指标
                system_data = data_dict.get('data', {})
                result.append({
                    'timestamp': data_dict['timestamp'],
                    'cpu_usage': system_data.get('cpu_usage', 0),
                    'memory_usage': system_data.get('memory_usage', 0),
                    'disk_usage': system_data.get('disk_usage', 0),
                    'network_in': system_data.get('network_in', 0),
                    'network_out': system_data.get('network_out', 0),
                    'load_average': system_data.get('load_average', 0)
                })
        
        # 按时间正序排列
        result.reverse()
        
        return jsonify({
            'status': 'success',
            'message': '系统监控数据获取成功',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"获取系统监控数据失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取系统监控数据失败: {str(e)}'
        }), 500


@monitor_bp.route('/system/current', methods=['GET'])
@jwt_required()
def get_system_current():
    """获取当前系统状态"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取最新的系统监控数据
        latest_data = MonitorData.query.filter_by(
            user_id=current_user_id,
            node_id=None,
            client_id=None
        ).order_by(MonitorData.timestamp.desc()).first()
        
        if not latest_data or not latest_data.data:
            # 如果没有数据，返回实时系统指标
            from backend.app.utils.utils import get_system_metrics
            system_metrics = get_system_metrics()
            return jsonify({
                'status': 'success',
                'message': '当前系统状态获取成功',
                'data': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'cpu_usage': system_metrics.get('cpu_usage', 0),
                    'memory_usage': system_metrics.get('memory_usage', 0),
                    'disk_usage': system_metrics.get('disk_usage', 0),
                    'network_in': system_metrics.get('network_in', 0),
                    'network_out': system_metrics.get('network_out', 0),
                    'load_average': system_metrics.get('load_avg', [0, 0, 0])[0] if system_metrics.get('load_avg') else 0
                }
            })
        
        # 返回最新的监控数据
        system_data = latest_data.data
        return jsonify({
            'status': 'success',
            'message': '当前系统状态获取成功',
            'data': {
                'timestamp': latest_data.timestamp.isoformat(),
                'cpu_usage': system_data.get('cpu_usage', 0),
                'memory_usage': system_data.get('memory_usage', 0),
                'disk_usage': system_data.get('disk_usage', 0),
                'network_in': system_data.get('network_in', 0),
                'network_out': system_data.get('network_out', 0),
                'load_average': system_data.get('load_average', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"获取当前系统状态失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取当前系统状态失败: {str(e)}'
        }), 500


@monitor_bp.route('/system/collect', methods=['POST'])
@jwt_required()
def collect_system_metrics():
    """手动触发系统指标收集"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取当前系统指标
        from backend.app.utils.utils import get_system_metrics
        system_metrics = get_system_metrics()
        
        # 创建监控数据记录
        monitor_data = MonitorData(
            user_id=current_user_id,
            node_id=None,  # 系统级别
            client_id=None,  # 系统级别
            data={
                'system': system_metrics,
                'timestamp': datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        
        db.session.add(monitor_data)
        db.session.commit()
        
        # 记录审计日志
        AuditService.log_system_operation(
            user_id=current_user_id,
            action='collect_metrics',
            details={'metrics': system_metrics},
            result='success'
        )
        
        return jsonify({
            'status': 'success',
            'message': '系统指标收集成功',
            'data': {
                'timestamp': monitor_data.timestamp.isoformat(),
                'metrics': system_metrics
            }
        })
        
    except Exception as e:
        logger.error(f"系统指标收集失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'系统指标收集失败: {str(e)}'
        }), 500