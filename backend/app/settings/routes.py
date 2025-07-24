from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models import NotificationSetting
from backend.app.notifications.services import NotificationService
from . import settings_bp

@settings_bp.route('/admin/notification', methods=['GET'])
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

@settings_bp.route('/admin/notification', methods=['POST'])
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

@settings_bp.route('', methods=['PUT'])
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

@settings_bp.route('', methods=['GET'])
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
    return jsonify({
        'status': 'success',
        'message': '系统设置获取成功',
        'data': result
    }) 