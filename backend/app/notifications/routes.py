from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.notifications.services import NotificationService
from backend.app.utils.decorators import handle_errors, require_user
from . import notifications_bp
from backend.app.models import User
from backend.app.utils.logger import get_logger
from backend.app.utils.type_matcher import TypeMatcher

logger = get_logger(__name__)

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

@notifications_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_notification_statistics():
    """获取通知统计信息"""
    try:
        user_id = get_jwt_identity()
        statistics = notification_service.get_notification_statistics(user_id)
        
        return jsonify({
            'status': 'success',
            'message': '通知统计获取成功',
            'data': statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting notification statistics: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取通知统计失败: {str(e)}'
        }), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_as_read():
    """标记所有通知为已读"""
    try:
        user_id = get_jwt_identity()
        updated_count = notification_service.mark_all_as_read(user_id)
        
        return jsonify({
            'status': 'success',
            'message': f'成功标记{updated_count}条通知为已读',
            'data': {
                'updated_count': updated_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return jsonify({
            'status': 'error',
            'message': f'标记通知为已读失败: {str(e)}'
        }), 500

@notifications_bp.route('/<string:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(notification_id):
    """标记单个通知为已读"""
    try:
        user_id = get_jwt_identity()
        success = notification_service.mark_as_read(notification_id, user_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '通知已标记为已读'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '通知不存在或标记失败'
            }), 404
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({
            'status': 'error',
            'message': f'标记通知为已读失败: {str(e)}'
        }), 500

@notifications_bp.route('/<string:notification_id>/unread', methods=['POST'])
@jwt_required()
def mark_as_unread(notification_id):
    """标记单个通知为未读"""
    try:
        user_id = get_jwt_identity()
        success = notification_service.mark_as_unread(notification_id, user_id)

        if success:
            return jsonify({
                'status': 'success',
                'message': '通知已标记为未读'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '通知不存在或标记失败'
            }), 404
        
    except Exception as e:
        logger.error(f"Error marking notification as unread: {e}")

@notifications_bp.route('/clear-all', methods=['POST'])
@jwt_required()
def clear_all_notifications():
    """清空所有通知"""
    try:
        user_id = get_jwt_identity()
        
        # 获取用户所有通知
        notifications = notification_service.get_user_notifications(user_id, limit=10000, offset=0)
        
        # 删除所有通知
        deleted_count = 0
        for notification in notifications:
            if notification_service.delete_notification(notification.id, user_id):
                deleted_count += 1
        
        return jsonify({
            'status': 'success',
            'message': f'成功清空{deleted_count}条通知',
            'data': {
                'deleted_count': deleted_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error clearing all notifications: {e}")
        return jsonify({
            'status': 'error',
            'message': f'清空通知失败: {str(e)}'
        }), 500

@notifications_bp.route('/cleanup', methods=['POST'])
@jwt_required()
def cleanup_old_notifications():
    """清理旧通知数据"""
    try:
        data = request.get_json()
        days = data.get('days', 90)
        
        deleted_count = notification_service.cleanup_old_notifications(days=days)
        
        return jsonify({
            'status': 'success',
            'message': f'成功清理{deleted_count}条旧通知数据',
            'data': {
                'deleted_count': deleted_count,
                'days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {e}")
        return jsonify({
            'status': 'error',
            'message': f'清理旧通知数据失败: {str(e)}'
        }), 500

@notifications_bp.route('/<string:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """删除通知"""
    try:
        user_id = get_jwt_identity()
        success = notification_service.delete_notification(notification_id, user_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '通知已删除'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '通知不存在或删除失败'
            }), 404
        
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        return jsonify({
            'status': 'error',
            'message': f'删除通知失败: {str(e)}'
        }), 500

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

@notifications_bp.route('/channels/<channel_id>/test', methods=['POST'])
@jwt_required()
@handle_errors
def test_notification_channel(channel_id):
    """测试通知渠道"""
    user_id = get_jwt_identity()
    notification_service.test_notification_channel(channel_id, user_id)
    return jsonify({'message': '通知渠道测试成功'})

@notifications_bp.route('/channels/<channel_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_notification_channel(channel_id):
    """删除通知渠道"""
    user_id = get_jwt_identity()
    notification_service.delete_channel(channel_id, user_id)
    return jsonify({'message': '通知渠道删除成功'})

@notifications_bp.route('/compatible-templates', methods=['GET'])
@jwt_required()
@handle_errors
def get_compatible_templates():
    """根据渠道类型获取兼容的模板"""
    user_id = get_jwt_identity()
    # 处理前端传递的数组参数格式
    channel_types = request.args.getlist('channel_types') or request.args.getlist('channel_types[]')
    
    if not channel_types:
        return jsonify({'templates': []})
    
    templates = TypeMatcher.get_compatible_templates(channel_types, user_id)
    
    return jsonify({'templates': templates})

@notifications_bp.route('/compatible-targets', methods=['GET'])
@jwt_required()
@handle_errors
def get_compatible_targets():
    """根据渠道类型获取兼容的通知对象"""
    user_id = get_jwt_identity()
    # 处理前端传递的数组参数格式
    channel_types = request.args.getlist('channel_types') or request.args.getlist('channel_types[]')
    
    if not channel_types:
        return jsonify({'targets': []})
    
    targets = TypeMatcher.get_compatible_targets(channel_types, user_id)
    
    return jsonify({'targets': targets})

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