# -*- coding: utf-8 -*-
from flask import request, jsonify, g
from . import commands_bp
from .service import RealTimeCommandService, StorageRealTimeService
from backend.app.utils.decorators import require_user
from backend.app.auth.services import AuditService
import logging

logger = logging.getLogger(__name__)

# 实时命令服务实例
command_service = RealTimeCommandService()
storage_realtime_service = StorageRealTimeService()


# ====================== Agent API 接口 ======================
# 这些接口供 Proxy Agent 调用

@commands_bp.route('/agent/<string:node_id>/commands', methods=['GET'])
def get_pending_commands(node_id):
    """Agent获取待执行的实时命令"""
    try:
        # 验证节点权限（可以加入token验证）
        commands = command_service.get_pending_commands(node_id)
        return jsonify({
            'status': 'success',
            'data': commands
        })
    except Exception as e:
        logger.error(f"获取待执行命令失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取命令失败: {str(e)}'
        }), 500


@commands_bp.route('/agent/<string:node_id>/commands/<string:command_id>/status', methods=['PUT'])
def update_command_status(node_id, command_id):
    """Agent更新命令执行状态"""
    try:
        status_data = request.get_json()
        if not status_data:
            return jsonify({
                'status': 'error',
                'message': '缺少状态数据'
            }), 400
        
        success = command_service.update_command_status(command_id, status_data)
        if success:
            return jsonify({
                'status': 'success',
                'message': '状态更新成功'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '状态更新失败'
            }), 400
            
    except Exception as e:
        logger.error(f"更新命令状态失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'更新状态失败: {str(e)}'
        }), 500


# ====================== 存储实时操作 API ======================
# 这些接口供前端调用

@commands_bp.route('/storage/<string:storage_id>/test-connection-realtime', methods=['POST'])
@require_user
def test_storage_connection_realtime(storage_id):
    """实时测试存储连接"""
    try:
        data = request.get_json()
        node_id = data.get('node_id') if data else None
        
        if not node_id:
            return jsonify({
                'status': 'error',
                'message': '请选择测试节点'
            }), 400
        
        # 记录审计日志
        AuditService.log_storage_operation(
            user_id=g.user.id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=None,
            details={'node_id': node_id, 'method': 'realtime'},
            result='started'
        )
        
        # 执行实时连接测试
        result = storage_realtime_service.test_connection_realtime(storage_id, node_id)
        
        # 记录结果
        AuditService.log_storage_operation(
            user_id=g.user.id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=None,
            details={'node_id': node_id, 'result': result},
            result='success' if result.get('status') == 'success' else 'failed'
        )
        
        return jsonify(result)
        
    except ValueError as e:
        AuditService.log_storage_operation(
            user_id=g.user.id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=None,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"实时连接测试失败: {e}")
        AuditService.log_storage_operation(
            user_id=g.user.id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=None,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 500


@commands_bp.route('/storage/<string:storage_id>/stats-realtime', methods=['GET'])
@require_user
def get_storage_stats_realtime(storage_id):
    """实时获取存储统计信息"""
    try:
        node_id = request.args.get('node_id')
        result = storage_realtime_service.get_storage_stats_realtime(storage_id, node_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取存储统计信息失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取统计信息失败: {str(e)}'
        }), 500


@commands_bp.route('/storage/<string:storage_id>/files-realtime', methods=['GET'])
@require_user
def list_files_realtime(storage_id):
    """实时获取文件列表"""
    try:
        path = request.args.get('path', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        node_id = request.args.get('node_id')
        
        result = storage_realtime_service.list_files_realtime(
            storage_id, path, page, page_size, node_id
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取文件列表失败: {str(e)}'
        }), 500


@commands_bp.route('/storage/<string:storage_id>/buckets-realtime', methods=['GET'])
@require_user
def list_buckets_realtime(storage_id):
    """实时获取存储桶列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        node_id = request.args.get('node_id')
        
        result = storage_realtime_service.list_buckets_realtime(
            storage_id, page, page_size, node_id
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取存储桶列表失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取存储桶列表失败: {str(e)}'
        }), 500


@commands_bp.route('/storage/<string:storage_id>/download-realtime', methods=['POST'])
@require_user
def download_file_realtime(storage_id):
    """实时下载文件"""
    try:
        data = request.get_json()
        file_path = data.get('file_path') if data else None
        bucket = data.get('bucket', '') if data else ''
        node_id = data.get('node_id') if data else None
        
        if not file_path:
            return jsonify({
                'status': 'error',
                'message': '文件路径不能为空'
            }), 400
        
        result = storage_realtime_service.download_file_realtime(
            storage_id, file_path, bucket, node_id
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'下载文件失败: {str(e)}'
        }), 500


# ====================== 命令管理 API ======================

@commands_bp.route('/commands/<string:command_id>', methods=['GET'])
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


@commands_bp.route('/commands/cleanup', methods=['POST'])
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