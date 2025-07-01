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