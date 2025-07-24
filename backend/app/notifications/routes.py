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

@notifications_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """获取系统通知设置（管理员专用）"""
    notification_service = NotificationService()
    try:
        settings = notification_service.get_system_settings()
        return jsonify(settings)
    except Exception as e:
        current_app.logger.error(f"获取系统通知设置失败: {str(e)}")
        return jsonify({"error": "获取系统通知设置失败"}), 500

@notifications_bp.route('/settings', methods=['POST'])
@jwt_required()
def save_notification_settings():
    """保存系统通知设置（管理员专用）"""
    notification_service = NotificationService()
    try:
        settings = request.json
        notification_service.save_system_settings(settings)
        return jsonify({"message": "系统通知设置保存成功"})
    except Exception as e:
        current_app.logger.error(f"保存系统通知设置失败: {str(e)}")
        return jsonify({"error": "保存系统通知设置失败"}), 500

@notifications_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """更新通知设置"""
    data = request.get_json()
    
    setting = NotificationSetting.query.filter_by(user_id=get_jwt_identity()).first()
    if not setting:
        setting = NotificationSetting(user_id=get_jwt_identity())
        db.session.add(setting)
    
    setting.enabled = data.get('enabled', setting.enabled)
    setting.email_enabled = data.get('email_enabled', setting.email_enabled)
    setting.webhook_enabled = data.get('webhook_enabled', setting.webhook_enabled)
    setting.webhook_url = data.get('webhook_url', setting.webhook_url)
    
    db.session.commit()
    
    return jsonify({
        'enabled': setting.enabled,
        'email_enabled': setting.email_enabled,
        'webhook_enabled': setting.webhook_enabled,
        'webhook_url': setting.webhook_url
    }) 

@notifications_bp.route('/system', methods=['GET'])
@jwt_required()
def get_system_settings():
    """统一系统设置接口，供前端Settings.vue使用"""
    # 基本设置（可根据实际情况从数据库或配置文件获取）
    basic_settings = {
        'max_concurrent_tasks': 5,
        'default_retry_count': 3,
        'default_retry_delay': 60,
        'notification_enabled': True
    }
    # 日志设置
    log_settings = {
        'log_retention_days': 30,
        'log_level': 'INFO',
        'log_file_path': '/var/log/easysync'
    }
    # 通知设置（可从NotificationService获取）
    notification_service = NotificationService()
    notification_settings = notification_service.get_system_settings()
    # 合并返回
    result = {**basic_settings, **log_settings, **notification_settings}
    return jsonify(result) 