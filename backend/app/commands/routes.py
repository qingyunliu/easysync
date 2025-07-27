# -*- coding: utf-8 -*-
from flask import request, jsonify, g
from . import commands_bp
from .service import RealTimeCommandService
from backend.app.utils.decorators import require_user
from backend.app.auth.services import AuditService
import logging

logger = logging.getLogger(__name__)

# 实时命令服务实例
command_service = RealTimeCommandService()

@commands_bp.route('/<string:command_id>', methods=['GET'])
@require_user
def get_command_status(command_id):
    """获取命令状态"""
    try:
        command = command_service.get_command_status(command_id)
        if not command:
            return jsonify({
                'status': 'error',
                'message': '命令不存在'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': command
        })
    except Exception as e:
        logger.error(f"获取命令状态失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取命令状态失败: {str(e)}'
        }), 500


@commands_bp.route('/cleanup', methods=['POST'])
@require_user
def cleanup_old_commands():
    """清理旧命令"""
    try:
        data = request.get_json()
        days = data.get('days', 7) if data else 7
        
        count = command_service.cleanup_old_commands(days)
        return jsonify({
            'status': 'success',
            'message': f'清理了 {count} 个旧命令',
            'count': count
        })
    except Exception as e:
        logger.error(f"清理旧命令失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'清理失败: {str(e)}'
        }), 500