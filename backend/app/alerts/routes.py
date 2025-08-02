from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.alerts.services import AlertPolicyService
from . import alerts_bp

alert_service = AlertPolicyService()

# =============== 告警策略相关路由 ===============

@alerts_bp.route('/policies', methods=['GET'])
@jwt_required()
def get_policies():
    """获取告警策略列表"""
    try:
        user_id = get_jwt_identity()
        category = request.args.get('category')
        enabled = request.args.get('enabled')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if enabled is not None:
            enabled = enabled.lower() == 'true'
        
        result = alert_service.get_policies(
            user_id=user_id,
            category=category,
            enabled=enabled,
            page=page,
            per_page=per_page
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/policies', methods=['POST'])
@jwt_required()
def create_policy():
    """创建告警策略"""
    try:
        user_id = get_jwt_identity()
        policy_data = request.json
        
        policy = alert_service.create_policy(user_id, policy_data)
        return jsonify(policy.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/policies/<policy_id>', methods=['GET'])
@jwt_required()
def get_policy(policy_id):
    """获取告警策略详情"""
    try:
        policy = alert_service.get_policy(policy_id)
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        return jsonify(policy.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/policies/<policy_id>', methods=['PUT'])
@jwt_required()
def update_policy(policy_id):
    """更新告警策略"""
    try:
        policy_data = request.json
        policy = alert_service.update_policy(policy_id, policy_data)
        
        return jsonify(policy.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/policies/<policy_id>', methods=['DELETE'])
@jwt_required()
def delete_policy(policy_id):
    """删除告警策略"""
    try:
        success = alert_service.delete_policy(policy_id)
        if success:
            return jsonify({'message': 'Policy deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete policy'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/policies/<policy_id>/rules', methods=['GET'])
@jwt_required()
def get_policy_rules(policy_id):
    """获取策略规则列表"""
    try:
        rules = alert_service.get_policy_rules(policy_id)
        return jsonify([rule.to_dict() for rule in rules])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/policies/<policy_id>/rules', methods=['POST'])
@jwt_required()
def create_policy_rule(policy_id):
    """创建策略规则"""
    try:
        rule_data = request.json
        rule = alert_service.create_policy_rule(policy_id, rule_data)
        
        return jsonify(rule.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============== 通知渠道相关路由 ===============

@alerts_bp.route('/notification-channels', methods=['GET'])
@jwt_required()
def get_notification_channels():
    """获取通知渠道列表"""
    try:
        user_id = get_jwt_identity()
        channel_type = request.args.get('type')
        
        channels = alert_service.get_notification_channels(
            user_id=user_id,
            channel_type=channel_type
        )
        
        return jsonify([channel.to_dict() for channel in channels])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/notification-channels', methods=['POST'])
@jwt_required()
def create_notification_channel():
    """创建通知渠道"""
    try:
        user_id = get_jwt_identity()
        channel_data = request.json
        
        channel = alert_service.create_notification_channel(user_id, channel_data)
        return jsonify(channel.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/notification-channels/<channel_id>/test', methods=['POST'])
@jwt_required()
def test_notification_channel(channel_id):
    """测试通知渠道"""
    try:
        success = alert_service.test_notification_channel(channel_id)
        
        if success:
            return jsonify({'message': '测试通知发送成功'})
        else:
            return jsonify({'error': '测试通知发送失败'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============== 通知对象相关路由 ===============

@alerts_bp.route('/notification-targets', methods=['GET'])
@jwt_required()
def get_notification_targets():
    """获取通知对象列表"""
    try:
        user_id = get_jwt_identity()
        target_type = request.args.get('type')
        
        targets = alert_service.get_notification_targets(
            user_id=user_id,
            target_type=target_type
        )
        
        return jsonify([target.to_dict() for target in targets])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/notification-targets', methods=['POST'])
@jwt_required()
def create_notification_target():
    """创建通知对象"""
    try:
        user_id = get_jwt_identity()
        target_data = request.json
        
        target = alert_service.create_notification_target(user_id, target_data)
        return jsonify(target.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============== 系统监控相关路由 ===============

@alerts_bp.route('/system/status', methods=['GET'])
@jwt_required()
def get_system_status():
    """获取系统监控状态"""
    try:
        # 这里可以获取系统各种状态信息
        status = {
            'cpu_usage': 65.4,
            'memory_usage': 72.8,
            'disk_usage': 45.2,
            'network_in': 1024.5,
            'network_out': 856.3,
            'active_connections': 156,
            'services_status': {
                'database': 'healthy',
                'redis': 'healthy',
                'queue': 'healthy'
            },
            'last_updated': '2024-01-20T10:30:00Z'
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_alert_statistics():
    """获取告警统计信息"""
    try:
        time_range = request.args.get('range', '24h')
        stats = alert_service.get_alert_statistics(time_range)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============== 预设配置相关路由 ===============

@alerts_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_policy_templates():
    """获取策略模板"""
    try:
        templates = [
            {
                'id': 'cpu_high',
                'name': 'CPU使用率过高',
                'category': 'system',
                'description': '当CPU使用率超过阈值时触发告警',
                'template': {
                    'conditions': {
                        'metric': 'cpu_usage',
                        'operator': '>',
                        'threshold': 80,
                        'duration': 300
                    },
                    'severity': 'warning'
                }
            },
            {
                'id': 'memory_high',
                'name': '内存使用率过高',
                'category': 'system',
                'description': '当内存使用率超过阈值时触发告警',
                'template': {
                    'conditions': {
                        'metric': 'memory_usage',
                        'operator': '>',
                        'threshold': 85,
                        'duration': 300
                    },
                    'severity': 'warning'
                }
            },
            {
                'id': 'disk_space_low',
                'name': '磁盘空间不足',
                'category': 'system',
                'description': '当磁盘使用率超过阈值时触发告警',
                'template': {
                    'conditions': {
                        'metric': 'disk_usage',
                        'operator': '>',
                        'threshold': 90,
                        'duration': 300
                    },
                    'severity': 'error'
                }
            },
            {
                'id': 'task_failure',
                'name': '任务执行失败',
                'category': 'task',
                'description': '当任务执行失败时触发告警',
                'template': {
                    'conditions': {
                        'metric': 'task_failure_rate',
                        'operator': '>',
                        'threshold': 5,
                        'duration': 60
                    },
                    'severity': 'error'
                }
            },
            {
                'id': 'storage_error',
                'name': '存储访问错误',
                'category': 'storage',
                'description': '当存储访问出现错误时触发告警',
                'template': {
                    'conditions': {
                        'metric': 'storage_error_rate',
                        'operator': '>',
                        'threshold': 1,
                        'duration': 60
                    },
                    'severity': 'error'
                }
            }
        ]
        
        return jsonify(templates)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_available_metrics():
    """获取可用的监控指标"""
    try:
        metrics = [
            {
                'name': 'cpu_usage',
                'display_name': 'CPU使用率',
                'category': 'system',
                'unit': '%',
                'description': '系统CPU使用百分比'
            },
            {
                'name': 'memory_usage',
                'display_name': '内存使用率',
                'category': 'system',
                'unit': '%',
                'description': '系统内存使用百分比'
            },
            {
                'name': 'disk_usage',
                'display_name': '磁盘使用率',
                'category': 'system',
                'unit': '%',
                'description': '磁盘空间使用百分比'
            },
            {
                'name': 'network_in',
                'display_name': '网络入流量',
                'category': 'network',
                'unit': 'Mbps',
                'description': '网络接收流量速率'
            },
            {
                'name': 'network_out',
                'display_name': '网络出流量',
                'category': 'network',
                'unit': 'Mbps',
                'description': '网络发送流量速率'
            },
            {
                'name': 'task_completion_rate',
                'display_name': '任务完成率',
                'category': 'task',
                'unit': '%',
                'description': '任务成功完成的百分比'
            },
            {
                'name': 'task_failure_rate',
                'display_name': '任务失败率',
                'category': 'task',
                'unit': 'count/min',
                'description': '每分钟失败的任务数'
            },
            {
                'name': 'storage_error_rate',
                'display_name': '存储错误率',
                'category': 'storage',
                'unit': 'count/min',
                'description': '每分钟存储访问错误数'
            },
            {
                'name': 'node_online_count',
                'display_name': '在线节点数',
                'category': 'node',
                'unit': 'count',
                'description': '当前在线的节点数量'
            },
            {
                'name': 'client_connection_count',
                'display_name': '客户端连接数',
                'category': 'client',
                'unit': 'count',
                'description': '当前活跃的客户端连接数'
            }
        ]
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500