from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models import MonitorData, Client, Node, Alert, AlertRule
from datetime import datetime, timedelta
from sqlalchemy import func
from . import monitor_bp
from .service import MonitorService
from .errors import MonitorError, MonitorNotFoundError, MonitorValidationError, MonitorOperationError, AlertRuleError
import logging
from backend.app.auth.services import AuditService

logger = logging.getLogger(__name__)

monitor_service = MonitorService()
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
            query = query.filter(MonitorData.timestamp >= datetime.fromisoformat(start_time))
        if end_time:
            query = query.filter(MonitorData.timestamp <= datetime.fromisoformat(end_time))
        
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

@monitor_bp.route('/alert-rules', methods=['POST'])
@jwt_required()
def create_alert_rule():
    """创建告警规则"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        rule = monitor_service.create_alert_rule(data)
        AuditService.log_operation(
            user_id=user_id,
            action='create',
            resource_type='monitor',
            resource_id=rule.id,
            resource_name=rule.name,
            details={'msg': '告警规则创建成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '告警规则创建成功',
            'data': rule.to_dict()
        }), 201
    except AlertRuleError as e:
        AuditService.log_operation(
            user_id=user_id,
            action='create',
            resource_type='monitor',
            resource_id=None,
            resource_name=data.get('name'),
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        AuditService.log_operation(
            user_id=user_id,
            action='create',
            resource_type='monitor',
            resource_id=None,
            resource_name=data.get('name'),
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'创建告警规则失败: {str(e)}'
        }), 500

@monitor_bp.route('/alert-rules', methods=['GET'])
@jwt_required()
def get_alert_rules():
    """获取告警规则列表"""
    rules = AlertRule.query.all()
    return jsonify({
        'status': 'success',
        'message': '告警规则列表获取成功',
        'data': [rule.to_dict() for rule in rules]
    })

@monitor_bp.route('/alert-rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_alert_rule(rule_id):
    """更新告警规则"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        rule = AlertRule.query.get(rule_id)
        
        if not rule:
            AuditService.log_operation(
                user_id=user_id,
                action='update',
                resource_type='monitor',
                resource_id=rule_id,
                resource_name=data.get('name'),
                details={'error': '告警规则不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '告警规则不存在'
            }), 404
            
        # 更新规则
        if 'name' in data:
            rule.name = data['name']
        if 'description' in data:
            rule.description = data['description']
        if 'metric' in data:
            rule.metric = data['metric']
        if 'operator' in data:
            rule.operator = data['operator']
        if 'threshold' in data:
            rule.threshold = data['threshold']
        if 'duration' in data:
            rule.duration = data['duration']
        if 'severity' in data:
            rule.severity = data['severity']
        if 'enabled' in data:
            rule.enabled = data['enabled']
            
        db.session.commit()
        
        AuditService.log_operation(
            user_id=user_id,
            action='update',
            resource_type='monitor',
            resource_id=rule.id,
            resource_name=rule.name,
            details={'msg': '告警规则更新成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '告警规则更新成功',
            'data': rule.to_dict()
        })
    except AlertRuleError as e:
        AuditService.log_operation(
            user_id=user_id,
            action='update',
            resource_type='monitor',
            resource_id=rule_id,
            resource_name=data.get('name'),
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        AuditService.log_operation(
            user_id=user_id,
            action='update',
            resource_type='monitor',
            resource_id=rule_id,
            resource_name=data.get('name'),
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'更新告警规则失败: {str(e)}'
        }), 500

@monitor_bp.route('/alert-rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_alert_rule(rule_id):
    """删除告警规则"""
    try:
        user_id = get_jwt_identity()
        rule = AlertRule.query.get(rule_id)
        
        if not rule:
            AuditService.log_operation(
                user_id=user_id,
                action='delete',
                resource_type='monitor',
                resource_id=rule_id,
                resource_name=None,
                details={'error': '告警规则不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '告警规则不存在'
            }), 404
            
        db.session.delete(rule)
        db.session.commit()
        
        AuditService.log_operation(
            user_id=user_id,
            action='delete',
            resource_type='monitor',
            resource_id=rule.id,
            resource_name=rule.name,
            details={'msg': '告警规则删除成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '告警规则删除成功'
        })
    except Exception as e:
        AuditService.log_operation(
            user_id=user_id,
            action='delete',
            resource_type='monitor',
            resource_id=rule_id,
            resource_name=None,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'删除告警规则失败: {str(e)}'
        }), 500

@monitor_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """获取告警列表"""
    user_id = get_jwt_identity()
    node_id = request.args.get('node_id')
    status = request.args.get('status', 'active')
    limit = int(request.args.get('limit', 100))
    
    if status == 'active':
        alerts = Alert.get_active_alerts(user_id=user_id, node_id=node_id, limit=limit)
    else:
        query = Alert.query.filter_by(user_id=user_id)
        if node_id:
            query = query.filter_by(node_id=node_id)
        if status != 'all':
            query = query.filter_by(status=status)
        alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'status': 'success',
        'message': '告警列表获取成功',
        'data': [alert.to_dict() for alert in alerts]
    })

@monitor_bp.route('/alerts/summary', methods=['GET'])
@jwt_required()
def get_alerts_summary():
    """获取告警汇总信息"""
    user_id = get_jwt_identity()
    summary = Alert.get_alert_summary(user_id=user_id)
    
    return jsonify({
        'status': 'success',
        'message': '告警汇总获取成功',
        'data': summary
    })

@monitor_bp.route('/alerts/<int:alert_id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_alert(alert_id):
    """解决告警"""
    user_id = get_jwt_identity()
    success = Alert.resolve_alert(alert_id, user_id=user_id)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': '告警已解决'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '告警解决失败'
        }), 400

@monitor_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['PUT'])
@jwt_required()
def acknowledge_alert(alert_id):
    """确认告警"""
    user_id = get_jwt_identity()
    data = request.get_json()
    acknowledged_by = data.get('acknowledged_by', user_id)
    
    success = Alert.acknowledge_alert(alert_id, acknowledged_by, user_id=user_id)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': '告警已确认'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '告警确认失败'
        }), 400

@monitor_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
@jwt_required()
def update_alert(alert_id):
    """更新告警状态"""
    data = request.get_json()
    alert = Alert.query.get(alert_id)
    
    if not alert:
        return jsonify({
            'status': 'error',
            'message': '告警不存在'
        }), 404
        
    # 更新告警状态
    if 'status' in data:
        alert.status = data['status']
    if 'resolution' in data:
        alert.resolution = data['resolution']
        
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '告警状态更新成功',
        'data': alert.to_dict()
    }) 