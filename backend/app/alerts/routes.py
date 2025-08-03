from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models.alert import AlertPolicy, NotificationChannel, NotificationTarget, AlertInstance
from backend.app.alerts.services import AlertService
from backend.app.utils.decorators import handle_errors, require_user
from . import alerts_bp
import logging

logger = logging.getLogger(__name__)

alert_service = AlertService()

@alerts_bp.route('/policies', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_policies():
    """获取告警策略列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    policy_type = request.args.get('policy_type', '')
    level = request.args.get('level', '')
    enabled = request.args.get('enabled', '')
    keyword = request.args.get('keyword', '')
    
    policies = alert_service.get_policies(
        user_id=user_id,
        page=page,
        per_page=per_page,
        policy_type=policy_type,
        level=level,
        enabled=enabled,
        keyword=keyword
    )
    
    return jsonify(policies)

@alerts_bp.route('/policies', methods=['POST'])
@jwt_required()
@handle_errors
def create_alert_policy():
    """创建告警策略"""
    data = request.get_json()
    user_id = get_jwt_identity()
    data['user_id'] = user_id
    
    policy = alert_service.create_policy(data)
    return jsonify({
        'message': '告警策略创建成功',
        'policy': policy.to_dict()
    }), 201

@alerts_bp.route('/policies/<policy_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_policy(policy_id):
    """获取告警策略详情"""
    user_id = get_jwt_identity()
    policy = alert_service.get_policy(policy_id, user_id)
    return jsonify(policy.to_dict())

@alerts_bp.route('/policies/<policy_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_alert_policy(policy_id):
    """更新告警策略"""
    data = request.get_json()
    user_id = get_jwt_identity()
    policy = alert_service.update_policy(policy_id, user_id, data)
    return jsonify({
        'message': '告警策略更新成功',
        'policy': policy.to_dict()
    })

@alerts_bp.route('/policies/<policy_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_alert_policy(policy_id):
    """删除告警策略"""
    user_id = get_jwt_identity()
    alert_service.delete_policy(policy_id, user_id)
    return jsonify({'message': '告警策略删除成功'})


@alerts_bp.route('/policies/<policy_id>/toggle', methods=['PUT'])
@jwt_required()
@handle_errors
def toggle_alert_policy(policy_id):
    """切换告警策略启用状态"""
    user_id = get_jwt_identity()
    policy = alert_service.toggle_policy(policy_id, user_id)
    return jsonify({
        'message': f'告警策略已{"启用" if policy.enabled else "禁用"}',
        'policy': policy.to_dict()
    })


@alerts_bp.route('/policies/<policy_id>/test', methods=['POST'])
@jwt_required()
@handle_errors
def test_alert_policy(policy_id):
    """测试告警策略"""
    user_id = get_jwt_identity()
    result = alert_service.test_policy(policy_id, user_id)
    return jsonify({
        'message': '告警策略测试完成',
        'result': result
    })

@alerts_bp.route('/statistics', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_statistics():
    """获取告警统计信息"""
    try:
        time_range = request.args.get('range', '24h')
        stats = alert_service.get_alert_statistics(time_range)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/channels', methods=['GET'])
@jwt_required()
@handle_errors
def get_notification_channels():
    """获取通知渠道列表"""
    user_id = get_jwt_identity()
    channels = alert_service.get_channels(user_id)
    return jsonify({'channels': channels})


@alerts_bp.route('/channels', methods=['POST'])
@jwt_required()
@handle_errors
def create_notification_channel():
    """创建通知渠道"""
    data = request.get_json()
    user_id = get_jwt_identity()
    data['user_id'] = user_id
    
    channel = alert_service.create_channel(data)
    return jsonify({
        'message': '通知渠道创建成功',
        'channel': channel.to_dict()
    }), 201


@alerts_bp.route('/channels/<channel_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_notification_channel(channel_id):
    """更新通知渠道"""
    data = request.get_json()
    user_id = get_jwt_identity()
    channel = alert_service.update_channel(channel_id, user_id, data)
    return jsonify({
        'message': '通知渠道更新成功',
        'channel': channel.to_dict()
    })


@alerts_bp.route('/channels/<channel_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_notification_channel(channel_id):
    """删除通知渠道"""
    alert_service.delete_channel(channel_id, current_user.id)
    return jsonify({'message': '通知渠道删除成功'})


@alerts_bp.route('/targets', methods=['GET'])
@jwt_required()
@handle_errors
def get_notification_targets():
    """获取通知对象列表"""
    user_id = get_jwt_identity()
    targets = alert_service.get_targets(user_id)
    return jsonify({'targets': targets})


@alerts_bp.route('/targets', methods=['POST'])
@jwt_required()
@handle_errors
def create_notification_target():
    """创建通知对象"""
    data = request.get_json()
    user_id = get_jwt_identity()
    data['user_id'] = user_id
    
    target = alert_service.create_target(data)
    return jsonify({
        'message': '通知对象创建成功',
        'target': target.to_dict()
    }), 201


@alerts_bp.route('/targets/<target_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_notification_target(target_id):
    """更新通知对象"""
    data = request.get_json()
    user_id = get_jwt_identity()
    target = alert_service.update_target(target_id, user_id, data)
    return jsonify({
        'message': '通知对象更新成功',
        'target': target.to_dict()
    })


@alerts_bp.route('/targets/<target_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_notification_target(target_id):
    """删除通知对象"""
    user_id = get_jwt_identity()
    alert_service.delete_target(target_id, user_id)
    return jsonify({'message': '通知对象删除成功'})


@alerts_bp.route('/instances', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_instances():
    """获取告警实例列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    severity = request.args.get('severity', '')
    
    instances = alert_service.get_instances(
        user_id=user_id,
        page=page,
        per_page=per_page,
        status=status,
        severity=severity
    )
    
    return jsonify(instances)


@alerts_bp.route('/instances/<instance_id>/resolve', methods=['PUT'])
@jwt_required()
@handle_errors
def resolve_alert_instance(instance_id):
    """解决告警实例"""
    user_id = get_jwt_identity()
    alert_service.resolve_instance(instance_id, user_id)
    return jsonify({'message': '告警已解决'})


@alerts_bp.route('/resources', methods=['GET'])
@jwt_required()
@handle_errors
def get_monitorable_resources():
    """获取可监控的资源列表"""
    user_id = get_jwt_identity()
    resources = alert_service.get_monitorable_resources(user_id)
    return jsonify({'resources': resources})


@alerts_bp.route('/events', methods=['GET'])
@jwt_required()
@handle_errors
def get_monitorable_events():
    """获取可监控的事件列表"""
    user_id = get_jwt_identity()
    events = alert_service.get_monitorable_events()
    return jsonify({'events': events})


@alerts_bp.route('/templates', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_templates():
    """获取告警策略模板"""
    user_id = get_jwt_identity()
    templates = alert_service.get_templates()
    return jsonify({'templates': templates})