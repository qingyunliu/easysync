from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models import NotificationSetting, SystemSetting
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
def update_system_settings():
    """统一保存所有设置（基本、日志、通知）"""
    data = request.get_json()
    user_id = get_jwt_identity()
    # 基本设置和日志设置
    for key in ['max_concurrent_tasks', 'default_retry_count', 'default_retry_delay', 'log_retention_days', 'log_level', 'log_file_path']:
        if key in data:
            s = SystemSetting.query.filter_by(key=key).first()
            if not s:
                s = SystemSetting(key=key, value=str(data[key]))
                db.session.add(s)
            else:
                s.value = str(data[key])
    # 通知设置
    notify = NotificationSetting.query.filter_by(user_id=user_id).first()
    if not notify:
        notify = NotificationSetting(user_id=user_id)
        db.session.add(notify)
    for field in [
        'enabled', 'email_enabled', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'email',
        'webhook_enabled', 'webhook_url', 'webhook_secret',
        'dingtalk_enabled', 'dingtalk_webhook', 'dingtalk_secret',
        'sms_enabled', 'sms_provider', 'sms_api_key', 'sms_template_id', 'sms_sign_name']:
        if field in data:
            setattr(notify, field, data[field])
    db.session.commit()
    return jsonify({'status': 'success', 'message': '设置已保存'})

@settings_bp.route('', methods=['GET'])
@jwt_required()
def get_system_settings():
    """统一系统设置接口，供前端Settings.vue使用"""
    # 从数据库读取基本设置和日志设置
    settings = {s.key: s.value for s in SystemSetting.query.all()}
    # 通知设置
    user_id = get_jwt_identity()
    notify = NotificationSetting.query.filter_by(user_id=user_id).first()
    notify_dict = notify.to_dict() if notify else {}
    # 合并返回
    result = {**settings, **notify_dict}
    return jsonify({
        'status': 'success',
        'message': '系统设置获取成功',
        'data': result
    }) 