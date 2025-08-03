from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.notifications.services import NotificationService
from backend.app.utils.decorators import handle_errors, require_user
from . import notifications_bp
from backend.app.models import User

notification_service = NotificationService()

@notifications_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """获取用户通知配置"""
    current_user_id = get_jwt_identity()
    config = notification_service.get_config(current_user_id)
    return jsonify(config)

@notifications_bp.route('/config', methods=['POST'])
@jwt_required()
def save_config():
    """保存用户通知配置"""
    current_user_id = get_jwt_identity()
    config_data = request.json
    notification_service.save_config(current_user_id, config_data)
    return jsonify({'message': '配置已保存'})

@notifications_bp.route('/test', methods=['POST'])
@jwt_required()
def test_notification():
    """测试通知发送（直接用前端传递的配置）"""
    config = request.json or {}
    user = User.query.get(get_jwt_identity())
    to_email = user.email if user else None
    try:
        notification_service.test_notification_config(config, to_email)
        return jsonify({'message': '测试通知已发送'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_settings():
    """获取用户通知设置"""
    settings = notification_service.get_system_settings()
    return jsonify(settings)

@notifications_bp.route('', methods=['POST'])
@jwt_required()
def save_settings():
    """保存用户通知设置"""
    settings = request.json
    notification_service.save_system_settings(settings)
    return jsonify({'message': '设置已保存'})

@notifications_bp.route('/list', methods=['GET'])
@jwt_required()
def get_notifications():
    """获取用户通知列表"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    notifications = notification_service.get_user_notifications(get_jwt_identity(), limit, offset)
    return jsonify([n.to_dict() for n in notifications])

@notifications_bp.route('/<string:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(notification_id):
    """标记通知为已读"""
    notification_service.mark_as_read(notification_id)
    return jsonify({'message': '通知已标记为已读'})

@notifications_bp.route('/<string:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """删除通知"""
    notification_service.delete_notification(notification_id)
    return jsonify({'message': '通知已删除'})

@notifications_bp.route('/channels', methods=['GET'])
@jwt_required()
@handle_errors
def get_notification_channels():
    """获取通知渠道列表"""
    user_id = get_jwt_identity()
    channels = notification_service.get_channels(user_id)
    return jsonify({'channels': channels})

@notifications_bp.route('/channels', methods=['POST'])
@jwt_required()
@handle_errors
def create_notification_channel():
    """创建通知渠道"""
    data = request.get_json()
    user_id = get_jwt_identity()
    data['user_id'] = user_id
    
    channel = notification_service.create_channel(data)
    return jsonify({
        'message': '通知渠道创建成功',
        'channel': channel.to_dict()
    }), 201

@notifications_bp.route('/channels/<channel_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_notification_channel(channel_id):
    """更新通知渠道"""
    data = request.get_json()
    user_id = get_jwt_identity()
    channel = notification_service.update_channel(channel_id, user_id, data)
    return jsonify({
        'message': '通知渠道更新成功',
        'channel': channel.to_dict()
    })

@notifications_bp.route('/channels/<channel_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_notification_channel(channel_id):
    """删除通知渠道"""
    user_id = get_jwt_identity()
    notification_service.delete_channel(channel_id, user_id)
    return jsonify({'message': '通知渠道删除成功'})

@notifications_bp.route('/targets', methods=['GET'])
@jwt_required()
@handle_errors
def get_notification_targets():
    """获取通知对象列表"""
    user_id = get_jwt_identity()
    targets = notification_service.get_targets(user_id)
    return jsonify({'targets': targets})

@notifications_bp.route('/targets', methods=['POST'])
@jwt_required()
@handle_errors
def create_notification_target():
    """创建通知对象"""
    data = request.get_json()
    user_id = get_jwt_identity()
    data['user_id'] = user_id
    
    target = notification_service.create_target(data)
    return jsonify({
        'message': '通知对象创建成功',
        'target': target.to_dict()
    }), 201

@notifications_bp.route('/targets/<target_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_notification_target(target_id):
    """更新通知对象"""
    data = request.get_json()
    user_id = get_jwt_identity()
    target = notification_service.update_target(target_id, user_id, data)
    return jsonify({
        'message': '通知对象更新成功',
        'target': target.to_dict()
    })

@notifications_bp.route('/targets/<target_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_notification_target(target_id):
    """删除通知对象"""
    user_id = get_jwt_identity()
    notification_service.delete_target(target_id, user_id)
    return jsonify({'message': '通知对象删除成功'})