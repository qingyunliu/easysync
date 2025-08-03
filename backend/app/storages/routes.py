from flask import current_app
from flask import request, jsonify, send_file
from . import storages_bp
from .services import StorageService
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.app.utils.decorators import require_user
import io
from botocore.exceptions import ClientError
from backend.app.auth.services import AuditService
from backend.app.storages.services import StorageRealTimeService
from backend.app.notifications.services import NotificationService
from backend.app.events.middleware import record_storage_event

storage_realtime_service = StorageRealTimeService()

storage_service = StorageService()
notification_service = NotificationService()

@storages_bp.route('', methods=['POST'])
@require_user
@record_storage_event('create')
def create_storage():
    """创建存储节点"""
    try:
        data = request.get_json()
        name = data.get('name')
        type = data.get('type')
        config = data.get('config', {})
        node_id = data.get('node_id')  # 获取节点ID
        user_id = get_jwt_identity()
        
        if not all([name, type]):
            AuditService.log_storage_operation(
                user_id=user_id,
                action='create',
                storage_id=None,
                storage_name=name,
                details={'error': '名称和类型不能为空'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '名称和类型不能为空'
            }), 400

        storage = storage_service.create_storage(name, type, config, node_id)
        
        # 发送存储创建通知
        notification_service.notify_storage_created(
            user_id=user_id,
            storage_name=storage.name,
            storage_type=storage.type
        )
        
        AuditService.log_storage_operation(
            user_id=user_id,
            action='create',
            storage_id=storage.id,
            storage_name=storage.name,
            details={'msg': '存储节点创建成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '存储节点创建成功',
            'storage': storage.to_dict()
        }), 201
    except ValueError as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='create',
            storage_id=None,
            storage_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='create',
            storage_id=None,
            storage_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'创建存储节点失败: {str(e)}'
        }), 500

@storages_bp.route('', methods=['GET'])
@require_user
@record_storage_event('list')
def get_storages():
    """获取存储节点列表"""
    try:
        storages = storage_service.get_storages()
        return jsonify({
            'status': 'success',
            'storages': [storage.to_dict() for storage in storages]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取存储节点列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>', methods=['GET'])
@require_user
@record_storage_event('get', lambda storage_id: storage_id)
def get_storage(storage_id):
    """获取存储节点详情"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        return jsonify({
            'status': 'success',
            'storage': storage.to_dict()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取存储节点详情失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>', methods=['PUT'])
@require_user
@record_storage_event('update', lambda storage_id: storage_id)
def update_storage(storage_id):
    """更新存储节点"""
    try:
        data = request.get_json()
        name = data.get('name')
        type = data.get('type')
        config = data.get('config', {})
        node_id = data.get('node_id')
        user_id = get_jwt_identity()
        
        if not all([name, type]):
            AuditService.log_storage_operation(
                user_id=user_id,
                action='update',
                storage_id=storage_id,
                storage_name=name,
                details={'error': '名称和类型不能为空'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '名称和类型不能为空'
            }), 400

        storage = storage_service.update_storage(storage_id, name, type, config, node_id)
        
        # 发送存储更新通知
        notification_service.notify_storage_updated(
            user_id=user_id,
            storage_name=storage.name,
            storage_type=storage.type
        )
        
        AuditService.log_storage_operation(
            user_id=user_id,
            action='update',
            storage_id=storage.id,
            storage_name=storage.name,
            details={'msg': '存储节点更新成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '存储节点更新成功',
            'storage': storage.to_dict()
        })
    except ValueError as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='update',
            storage_id=storage_id,
            storage_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='update',
            storage_id=storage_id,
            storage_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'更新存储节点失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>', methods=['DELETE'])
@require_user
@record_storage_event('delete', lambda storage_id: storage_id)
def delete_storage(storage_id):
    """删除存储节点"""
    try:
        user_id = get_jwt_identity()
        
        # 获取存储信息用于审计
        storage = storage_service.get_storage(storage_id)
        storage_name = storage.name if storage else 'unknown'
        
        storage_service.delete_storage(storage_id)
        
        # 发送存储删除通知
        if storage:
            notification_service.notify_storage_deleted(
                user_id=user_id,
                storage_name=storage.name,
                storage_type=storage.type
            )
        
        AuditService.log_storage_operation(
            user_id=user_id,
            action='delete',
            storage_id=storage_id,
            storage_name=storage_name,
            details={'msg': '存储节点删除成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '存储节点删除成功'
        })
    except ValueError as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='delete',
            storage_id=storage_id,
            storage_name='unknown',
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='delete',
            storage_id=storage_id,
            storage_name='unknown',
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'删除存储节点失败: {str(e)}'
        }), 500

@storages_bp.route('/test-connection', methods=['POST'])
@require_user
@record_storage_event('test_connection')
def test_temporary_connect():
    """测试临时连接"""
    try:
        data = request.get_json()
        type = data.get('type')
        config = data.get('config', {})
        
        if not type:
            return jsonify({
                'status': 'error',
                'message': '存储类型不能为空'
            }), 400
        
        # 测试连接
        result = storage_service.test_connection(type, config)
        
        return jsonify({
            'status': 'success',
            'message': '连接测试成功',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/test-connection', methods=['POST'])
@require_user
@record_storage_event('test_connection', lambda storage_id: storage_id)
def test_storage_connection(storage_id):
    """测试存储连接"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        # 测试连接
        result = storage_service.test_storage_connection(storage)
        
        return jsonify({
            'status': 'success',
            'message': '连接测试成功',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/stats', methods=['GET'])
@require_user
@record_storage_event('get_stats', lambda storage_id: storage_id)
def get_storage_stats(storage_id):
    """获取存储统计信息"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        stats = storage_service.get_storage_stats(storage)
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取存储统计失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/buckets', methods=['GET'])
@require_user
@record_storage_event('list_buckets', lambda storage_id: storage_id)
def list_buckets(storage_id):
    """获取存储桶列表"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        buckets = storage_service.list_buckets(storage)
        
        return jsonify({
            'status': 'success',
            'buckets': buckets
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取存储桶列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/objects', methods=['GET'])
@require_user
@record_storage_event('list_objects', lambda storage_id: storage_id)
def list_objects(storage_id):
    """获取对象列表"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        bucket = request.args.get('bucket')
        prefix = request.args.get('prefix', '')
        delimiter = request.args.get('delimiter', '/')
        
        if not bucket:
            return jsonify({
                'status': 'error',
                'message': '存储桶名称不能为空'
            }), 400
        
        objects = storage_service.list_objects(storage, bucket, prefix, delimiter)
        
        return jsonify({
            'status': 'success',
            'objects': objects
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取对象列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/files', methods=['GET'])
@require_user
@record_storage_event('list_files', lambda storage_id: storage_id)
def list_files(storage_id):
    """获取文件列表"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        path = request.args.get('path', '/')
        
        files = storage_service.list_files(storage, path)
        
        return jsonify({
            'status': 'success',
            'files': files
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取文件列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/download', methods=['POST'])
@require_user
@record_storage_event('download', lambda storage_id: storage_id)
def download_file(storage_id):
    """下载文件"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({
                'status': 'error',
                'message': '文件路径不能为空'
            }), 400
        
        file_data = storage_service.download_file(storage, file_path)
        
        return send_file(
            io.BytesIO(file_data),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=file_path.split('/')[-1]
        )
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'下载文件失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/mount-check', methods=['POST'])
@require_user
@record_storage_event('mount_check', lambda storage_id: storage_id)
def mount_check(storage_id):
    """检查挂载状态"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        result = storage_service.check_mount_status(storage)
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'检查挂载状态失败: {str(e)}'
        }), 500