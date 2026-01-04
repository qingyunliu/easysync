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
            'message': '存储节点列表获取成功',
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
            'message': '存储节点详情获取成功',
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
        
        storage = storage_service.update_storage(storage_id, name, type, config, node_id)
        if not storage:
            AuditService.log_storage_operation(
                user_id=user_id,
                action='update',
                storage_id=storage_id,
                storage_name=name,
                details={'error': '存储节点不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404

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
        if not storage:
            AuditService.log_storage_operation(
                user_id=user_id,
                action='delete',
                storage_id=storage_id,
                storage_name=None,
                details={'error': '存储节点不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404

        storage_name = storage.name
        storage_type = storage.type
        
        # 发送存储删除通知（在删除之前发送）
        notification_service.notify_storage_deleted(
            user_id=user_id,
            storage_name=storage_name,
            storage_type=storage_type
        )
        
        storage_service.delete_storage(storage_id)
        
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
        storage_type = data.get('type')
        config = data.get('config', {})
        node_id = data.get('node_id')
        
        if not storage_type:
            return jsonify({
                'status': 'error',
                'message': '存储类型不能为空'
            }), 400
        
        if not node_id:
            return jsonify({
                'status': 'error',
                'message': '请选择测试节点'
            }), 400
        
        # 构建测试参数
        params = {
            'storage_config': {
                'id': 'temp',  # 临时测试，使用临时ID
                'name': '临时测试',
                'type': storage_type,
                'config': config
            }
        }
        
        # 执行实时命令测试连接
        result = storage_realtime_service.command_service.execute_command_sync(
            node_id=node_id,
            command_type='test_connection',
            params=params,
            timeout=30
        )
        
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
    """实时测试存储连接"""
    try:
        data = request.get_json()
        node_id = data.get('node_id') if data else None
        user_id = get_jwt_identity()
        storage = storage_service.get_storage(storage_id)
        
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        
        if not node_id:
            return jsonify({
                'status': 'error',
                'message': '请选择测试节点'
            }), 400
        
        # 记录审计日志
        AuditService.log_storage_operation(
            user_id=user_id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'node_id': node_id, 'method': 'realtime'},
            result='started'
        )
        
        # 执行实时连接测试
        result = storage_realtime_service.test_connection_realtime(storage_id, node_id)
        
        # 根据测试结果发送通知
        if result.get('status') == 'success':
            notification_service.notify_storage_connected(
                user_id=user_id,
                storage_name=storage.name,
                storage_type=storage.type
            )
        else:
            notification_service.notify_storage_disconnected(
                user_id=user_id,
                storage_name=storage.name,
                reason=result.get('message', '连接测试失败')
            )
        
        # 记录结果
        AuditService.log_storage_operation(
            user_id=user_id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'node_id': node_id, 'result': result},
            result='success' if result.get('status') == 'success' else 'failed'
        )
        
        return jsonify(result)
        
    except ValueError as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"实时连接测试失败: {e}")
        AuditService.log_storage_operation(
            user_id=user_id,
            action='test_connection_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/stats', methods=['GET'])
@require_user
@record_storage_event('get_stats', lambda storage_id: storage_id)
def get_storage_stats(storage_id):
    """实时获取存储统计信息"""
    try:
        node_id = request.args.get('node_id')
        user_id = get_jwt_identity()
        storage = storage_service.get_storage(storage_id)
        result = storage_realtime_service.get_storage_stats_realtime(storage_id, node_id)
        AuditService.log_storage_operation(
            user_id=user_id,
            action='get_stats_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': '获取存储统计信息', 'result': result},
            result='success'
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"获取存储统计信息失败: {e}")
        AuditService.log_storage_operation(
            user_id=user_id,
            action='get_stats_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'error': str(e), 'result': None},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/buckets', methods=['GET'])
@require_user
@record_storage_event('list_buckets', lambda storage_id: storage_id)
def list_buckets(storage_id):
    """实时获取存储桶列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        node_id = request.args.get('node_id')
        user_id = get_jwt_identity()
        storage = storage_service.get_storage(storage_id)

        if not storage:
            return jsonify({'status': 'error', 'message': '存储节点不存在'}), 404
        
        if not node_id:
            if not storage.node_id:
                return jsonify({'status': 'error', 'message': '该存储未绑定任何节点，无法获取存储桶列表'}), 400
            node_id = storage.node_id
        
        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_buckets_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': '获取存储桶列表'},
            result='started'
        )

        result = storage_realtime_service.list_buckets_realtime(
            storage_id, page, page_size, node_id
        )

        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_buckets_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': '获取存储桶列表', 'result': result},
            result='success'
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"获取存储桶列表失败: {e}")
        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_buckets_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'获取存储桶列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/objects', methods=['GET'])
@require_user
@record_storage_event('list_objects', lambda storage_id: storage_id)
def list_objects(storage_id):
    """实时获取对象存储objects列表"""
    try:
        user_id = get_jwt_identity()
        node_id = request.args.get("node_id")
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({'status': 'error', 'message': '存储不存在'}), 404

        # 检查存储是否有绑定的节点
        if not node_id:
            return jsonify({'status': 'error', 'message': '请选择节点'}), 400

        # 只支持S3/OBS类型
        if storage.type not in ['s3', 'obs']:
            return jsonify({'status': 'error', 'message': '仅支持对象存储类型'}), 400

        # 获取参数
        bucket = request.args.get('bucket', storage.config.get('bucket', ''))
        prefix = request.args.get('prefix', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        if not bucket:
            return jsonify({
                'status': 'error',
                'message': '存储桶名称不能为空'
            }), 400        

        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_objects_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': f'开始获取{bucket}对象列表'},
            result='started'
        )

        # 调用agent实时获取对象列表
        result = storage_realtime_service.list_objects_realtime(
            storage_id=storage_id,
            bucket=bucket,
            prefix=prefix,
            page=page,
            page_size=page_size,
            node_id=node_id
        )

        if result.get('status') == 'error':
            AuditService.log_storage_operation(
                user_id=user_id,
                action='list_objects_realtime',
                storage_id=storage_id,
                storage_name=storage.name,
                details={'msg': f'获取{bucket}对象列表错误', 'result': result},
                result='failed'
            ) 
            return jsonify({'status': 'error', 'message': result.get('message', '获取失败')}), 500
        
        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_objects_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': f'获取{bucket}对象列表成功', 'result': result},
            result='success'
        )

        return jsonify({
            'status': 'success',
            'data': result.get('data', []),
            'total': result.get('total', 0),
            'page': page,
            'page_size': page_size
        })

    except Exception as e:
        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_objects_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({'status': 'error', 'message': str(e)}), 500

@storages_bp.route('/<string:storage_id>/files', methods=['GET'])
@require_user
@record_storage_event('list_files', lambda storage_id: storage_id)
def list_files(storage_id):
    """实时获取文件列表"""
    try:
        path = request.args.get('path', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        node_id = request.args.get('node_id')
        user_id = get_jwt_identity()
        storage = storage_service.get_storage(storage_id)

        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_files_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': '获取文件列表'},
            result='started'
        )
        
        result = storage_realtime_service.list_files_realtime(
            storage_id=storage_id,
            path=path,
            page=page,
            page_size=page_size,
            node_id=node_id
        )

        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_files_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': '获取文件列表', 'result': result},
            result='success'
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"获取文件列表失败: {e}")
        AuditService.log_storage_operation(
            user_id=user_id,
            action='list_files_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'获取文件列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/download', methods=['POST'])
@require_user
@record_storage_event('download', lambda storage_id: storage_id)
def download_file(storage_id):
    """实时下载文件"""
    try:
        data = request.get_json()
        path = data.get('path') if data else None
        bucket = data.get('bucket', '') if data else ''
        node_id = data.get('node_id') if data else None
        user_id = get_jwt_identity()
        storage = storage_service.get_storage(storage_id)
        
        if not path:
            return jsonify({
                'status': 'error',
                'message': '文件路径不能为空'
            }), 400
        
        AuditService.log_storage_operation(
            user_id=user_id,
            action='download_file_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': '下载文件', 'result': result},
            result='started'
        )
        result = storage_realtime_service.download_file_realtime(
            storage_id, path, bucket, node_id
        )
        AuditService.log_storage_operation(
            user_id=user_id,
            action='download_file_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'msg': '下载文件', 'result': result},
            result='success' if result.get('status') == 'success' else 'failed'
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"下载文件失败: {e}")
        AuditService.log_storage_operation(
            user_id=user_id,
            action='download_file_realtime',
            storage_id=storage_id,
            storage_name=storage.name,
            details={'error': str(e)},
            result='failed'
        )
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

        if storage.type not in ['nas', 'nfs']:
            return jsonify({'status': 'error', 'message': '仅支持 NAS/NFS 挂载检测'}), 400
        
        result = storage_realtime_service.check_mount_status_realtime(storage)
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'检查挂载状态失败: {str(e)}'
        }), 500