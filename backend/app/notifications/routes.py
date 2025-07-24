from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models import NotificationSetting
from backend.app.notifications.services import NotificationService
from . import notifications_bp
from backend.app.utils.decorators import admin_required
from backend.app.config.default import Config

@notifications_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """获取用户通知配置"""
    current_user_id = get_jwt_identity()
    notification_service = NotificationService()
    config = notification_service.get_config(current_user_id)
    return jsonify(config)

@notifications_bp.route('/config', methods=['POST'])
@jwt_required()
def save_config():
    """保存用户通知配置"""
    current_user_id = get_jwt_identity()
    notification_service = NotificationService()
    config_data = request.json
    notification_service.save_config(current_user_id, config_data)
    return jsonify({'message': '配置已保存'})

@notifications_bp.route('/test', methods=['POST'])
@jwt_required()
def test_notification():
    """测试通知发送"""
    notification_service = NotificationService()
    config = request.json
    notification_service.test_notification(get_jwt_identity(), config)
    return jsonify({'message': '测试通知已发送'})

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_settings():
    """获取用户通知设置"""
    notification_service = NotificationService()
    settings = notification_service.get_system_settings()
    return jsonify(settings)

@notifications_bp.route('', methods=['POST'])
@jwt_required()
def save_settings():
    """保存用户通知设置"""
    notification_service = NotificationService()
    settings = request.json
    notification_service.save_system_settings(settings)
    return jsonify({'message': '设置已保存'})

@notifications_bp.route('/list', methods=['GET'])
@jwt_required()
def get_notifications():
    """获取用户通知列表"""
    notification_service = NotificationService()
    limit = request.args.get('limit', 100, type=int)
    notifications = notification_service.get_user_notifications(get_jwt_identity(), limit)
    return jsonify([n.to_dict() for n in notifications])

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(notification_id):
    """标记通知为已读"""
    notification_service = NotificationService()
    notification_service.mark_as_read(notification_id)
    return jsonify({'message': '通知已标记为已读'})

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """删除通知"""
    notification_service = NotificationService()
    notification_service.delete_notification(notification_id)
    return jsonify({'message': '通知已删除'})