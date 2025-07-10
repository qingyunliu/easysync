from flask import request, jsonify, send_file
from . import storages_bp
from .services import StorageService
from backend.app.utils.decorators import require_user
import io
from botocore.exceptions import ClientError

storage_service = StorageService()

@storages_bp.route('', methods=['POST'])
@require_user
def create_storage():
    """创建存储节点"""
    try:
        data = request.get_json()
        name = data.get('name')
        type = data.get('type')
        config = data.get('config', {})
        
        if not all([name, type]):
            return jsonify({
                'status': 'error',
                'message': '名称和类型不能为空'
            }), 400

        storage = storage_service.create_storage(name, type, config)
        return jsonify({
            'status': 'success',
            'message': '存储节点创建成功',
            'storage': storage.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'创建存储节点失败: {str(e)}'
        }), 500

@storages_bp.route('', methods=['GET'])
@require_user
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
def update_storage(storage_id):
    """更新存储节点"""
    try:
        data = request.get_json()
        name = data.get('name')
        type = data.get('type')
        config = data.get('config')
        
        storage = storage_service.update_storage(storage_id, name, type, config)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        return jsonify({
            'status': 'success',
            'message': '存储节点更新成功',
            'storage': storage.to_dict()
        })
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'更新存储节点失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>', methods=['DELETE'])
@require_user
def delete_storage(storage_id):
    """删除存储节点"""
    try:
        if not storage_service.delete_storage(storage_id):
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
        return '', 204
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'删除存储节点失败: {str(e)}'
        }), 500

@storages_bp.route('/test-connection', methods=['POST'])
@require_user
def test_temporary_connect():
    """创建前临时进行连接测试"""
    try:
        data = request.get_json()
        storage_type = data.get('type')
        config = data.get('config', {})
        
        if not storage_type:
            return jsonify({
                'status': 'error',
                'message': '存储类型不能为空'
            }), 400
            
        # 创建临时存储对象
        temp_storage = type('TempStorage', (), {'type': storage_type, 'config': config})
        result = storage_service.test_connection(temp_storage)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/test-connection', methods=['POST'])
@require_user
def test_connect(storage_id):
    """测试存储连接"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        result = storage_service.test_connection(storage)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/stats', methods=['GET'])
@require_user
def get_storage_stats(storage_id):
    """获取存储统计信息"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        stats = storage_service.get_stats(storage)
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/buckets', methods=['GET'])
@require_user
def get_buckets(storage_id):
    """获取存储桶列表"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        buckets = storage_service.list_buckets(storage, page, page_size)
        return jsonify({
            'status': 'success',
            'data': buckets
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取存储桶列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/objects', methods=['GET'])
@require_user
def get_objects(storage_id):
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
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        if not bucket:
            return jsonify({
                'status': 'error',
                'message': '存储桶名称不能为空'
            }), 400

        result = storage_service.list_objects(storage, bucket, prefix, page, page_size)
        return jsonify({
            'status': 'success',
            'data': result
        })
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取对象列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/download', methods=['GET'])
@require_user
def download_object(storage_id):
    """下载对象"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        bucket = request.args.get('bucket')
        key = request.args.get('key')
        
        if not bucket or not key:
            return jsonify({
                'status': 'error',
                'message': '存储桶名称和对象键不能为空'
            }), 400
        
        data = storage_service.download_object(storage, bucket, key)
        filename = key.split('/')[-1]
        
        return send_file(
            io.BytesIO(data),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'下载对象失败: {str(e)}'
        }), 500

# NAS 存储相关 API
@storages_bp.route('/<string:storage_id>/nas/stats', methods=['GET'])
@require_user
def get_nas_stats(storage_id):
    """获取 NAS 存储统计信息"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        if storage.type != 'nas':
            return jsonify({
                'status': 'error',
                'message': '该存储不是 NAS 类型'
            }), 400
            
        stats = storage_service.get_nas_stats(storage)
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取 NAS 统计信息失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/nas/files', methods=['GET'])
@require_user
def get_nas_files(storage_id):
    """获取 NAS 文件列表"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        if storage.type != 'nas':
            return jsonify({
                'status': 'error',
                'message': '该存储不是 NAS 类型'
            }), 400
            
        path = request.args.get('path', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        result = storage_service.list_nas_files(storage, path, page, page_size)
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取文件列表失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/nas/download', methods=['GET'])
@require_user
def download_nas_file(storage_id):
    """下载 NAS 文件"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        if storage.type != 'nas':
            return jsonify({
                'status': 'error',
                'message': '该存储不是 NAS 类型'
            }), 400
            
        path = request.args.get('path')
        if not path:
            return jsonify({
                'status': 'error',
                'message': '文件路径不能为空'
            }), 400
        
        data = storage_service.download_nas_file(storage, path)
        filename = path.split('/')[-1]
        
        return send_file(
            io.BytesIO(data),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'下载文件失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/info', methods=['GET'])
@require_user
def get_storage_info(storage_id):
    """获取存储信息（兼容前端）"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({
                'status': 'error',
                'message': '存储节点不存在'
            }), 404
            
        if storage.type == 'nas':
            stats = storage_service.get_nas_stats(storage)
        else:
            stats = storage_service.get_stats(storage)
            
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取存储信息失败: {str(e)}'
        }), 500

@storages_bp.route('/<string:storage_id>/mount-check', methods=['POST'])
@require_user
def mount_check(storage_id):
    """检测 NAS/NFS 存储挂载状态"""
    try:
        storage = storage_service.get_storage(storage_id)
        if not storage:
            return jsonify({'status': 'error', 'message': '存储节点不存在'}), 404
        if storage.type not in ['nas', 'nfs']:
            return jsonify({'status': 'error', 'message': '仅支持 NAS/NFS 挂载检测'}), 400
        result = storage_service.mount_check(storage)
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'挂载检测失败: {str(e)}'}), 500