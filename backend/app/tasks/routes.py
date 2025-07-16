from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.models import Task, TaskLog
from . import tasks_bp
from .service import TaskService
from datetime import datetime
import logging
from .errors import TaskError, TaskNotFoundError, TaskOperationError, TaskValidationError, TaskStateError

logger = logging.getLogger(__name__)

task_service = TaskService()

@tasks_bp.errorhandler(TaskError)
def handle_task_error(error):
    """处理任务错误"""
    if isinstance(error, TaskNotFoundError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 404
    elif isinstance(error, TaskValidationError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
    elif isinstance(error, TaskStateError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
    elif isinstance(error, TaskOperationError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
    else:
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 500

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """获取任务列表"""
    user_id = get_jwt_identity()
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify({
        'status': 'success',
        'message': '任务列表获取成功',
        'data': [task.to_dict() for task in tasks]
    })

@tasks_bp.route('/<string:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """获取任务详情（包含存储配置信息）"""
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({
            'status': 'error',
            'message': '任务不存在'
        }), 404
    return jsonify({
        'status': 'success',
        'message': '任务详情获取成功',
        'data': task.to_dict_with_storage_config()
    })

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """创建任务，支持 type=mount-check（如挂载检测），允许 node_id/source/options 字段"""
    user_id = get_jwt_identity()
    data = request.get_json()
    data['user_id'] = user_id
    
    try:
        task = task_service.create_task(data)
        return jsonify({
            'status': 'success',
            'message': '任务创建成功',
            'data': task.to_dict()
        }), 201
    except TaskValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@tasks_bp.route('/<string:task_id>/status', methods=['PUT'])
@jwt_required()
def update_task_status(task_id):
    """更新任务状态"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        task = task_service.update_task_status(task_id, data)
        return jsonify({
            'status': 'success',
            'message': '任务状态更新成功',
            'data': task.to_dict()
        })
    except TaskNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except TaskStateError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@tasks_bp.route('/node/<string:node_id>', methods=['GET'])
@jwt_required()
def get_node_tasks(node_id):
    """获取节点任务（包含存储配置信息）"""
    try:
        tasks = task_service.get_node_tasks(node_id)
        return jsonify({
            'status': 'success',
            'message': '获取任务成功',
            'data': [task.to_dict_with_storage_config() for task in tasks]
        })
    except TaskOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@tasks_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_tasks():
    """获取待分配任务"""
    try:
        tasks = task_service.get_pending_tasks()
        return jsonify({
            'status': 'success',
            'message': '获取任务成功',
            'data': [task.to_dict() for task in tasks]
        })
    except TaskOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@tasks_bp.route('/<string:task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_task(task_id):
    """取消任务"""
    user_id = get_jwt_identity()
    
    try:
        task = task_service.cancel_task(task_id)
        return jsonify({
            'status': 'success',
            'message': '任务取消成功',
            'data': task.to_dict()
        })
    except TaskNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except TaskOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@tasks_bp.route('/<string:task_id>/retry', methods=['POST'])
@jwt_required()
def retry_task(task_id):
    """重试任务"""
    user_id = get_jwt_identity()
    
    try:
        task = task_service.retry_task(task_id)
        return jsonify({
            'status': 'success',
            'message': '任务重试成功',
            'data': task.to_dict()
        })
    except TaskNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except TaskOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@tasks_bp.route('/<string:task_id>/assign', methods=['POST'])
@jwt_required()
def assign_task(task_id):
    """分配任务"""
    user_id = get_jwt_identity()
    data = request.get_json()
    node_id = data.get('node_id')
    
    try:
        task = task_service.assign_task(task_id, node_id)
        return jsonify({
            'status': 'success',
            'message': '任务分配成功',
            'data': task.to_dict()
        })
    except TaskNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except TaskOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@tasks_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_all_task_logs():
    """获取当前用户所有任务日志列表"""
    current_user_id = get_jwt_identity()
    logs = TaskLog.query.filter_by(user_id=current_user_id).order_by(TaskLog.created_at.desc()).all()
    return jsonify({
        'status': 'success',
        'message': '任务日志列表获取成功',
        'logs': [log.to_dict() for log in logs]
    })

@tasks_bp.route('/<string:task_id>/start', methods=['POST'])
@jwt_required()
def start_task(task_id):
    """启动任务"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user_id:
        return jsonify({'error': '任务不属于当前用户'}), 403
    if task_service.start_task(task_id):
        return jsonify({
            'status': 'success',
            'message': '任务已启动'
        })
    return jsonify({
        'status': 'error',
        'message': '任务启动失败'
    }), 500

@tasks_bp.route('/<string:task_id>/logs', methods=['GET'])
@jwt_required()
def get_task_logs(task_id):
    """获取任务详细日志"""
    user_id = get_jwt_identity()
    
    try:
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404
        
        logs = task_service.get_task_logs(task_id)
        return jsonify({
            'status': 'success',
            'message': '任务日志获取成功',
            'data': [log.to_dict() for log in logs]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取任务日志失败: {str(e)}'
        }), 500

@tasks_bp.route('/<string:task_id>/logs/summary', methods=['GET'])
@jwt_required()
def get_task_execution_summary(task_id):
    """获取任务执行摘要"""
    user_id = get_jwt_identity()
    
    try:
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404
        
        summary = task_service.get_task_execution_summary(task_id)
        return jsonify({
            'status': 'success',
            'message': '任务执行摘要获取成功',
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取任务执行摘要失败: {str(e)}'
        }), 500

@tasks_bp.route('/<string:task_id>/logs/step', methods=['POST'])
@jwt_required()
def add_task_step_log(task_id):
    """添加任务步骤日志"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404
        
        step_name = data.get('step_name')
        step_status = data.get('step_status')
        step_message = data.get('step_message')
        step_details = data.get('step_details', {})
        
        if not all([step_name, step_status, step_message]):
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        log = task_service.add_task_step_log(task_id, step_name, step_status, step_message, step_details)
        return jsonify({
            'status': 'success',
            'message': '步骤日志添加成功',
            'data': log.to_dict()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'添加步骤日志失败: {str(e)}'
        }), 500

@tasks_bp.route('/<string:task_id>/logs/progress', methods=['POST'])
@jwt_required()
def add_task_progress_log(task_id):
    """添加任务进度日志"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404
        
        progress = data.get('progress')
        current_step = data.get('current_step')
        total_steps = data.get('total_steps')
        step_details = data.get('step_details', {})
        
        if progress is None or not current_step or not total_steps:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        log = task_service.add_task_progress_log(task_id, progress, current_step, total_steps, step_details)
        return jsonify({
            'status': 'success',
            'message': '进度日志添加成功',
            'data': log.to_dict()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'添加进度日志失败: {str(e)}'
        }), 500

@tasks_bp.route('/<string:task_id>/logs/error', methods=['POST'])
@jwt_required()
def add_task_error_log(task_id):
    """添加任务错误日志"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404
        
        error_type = data.get('error_type')
        error_message = data.get('error_message')
        error_details = data.get('error_details', {})
        
        if not all([error_type, error_message]):
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        log = task_service.add_task_error_log(task_id, error_type, error_message, error_details)
        return jsonify({
            'status': 'success',
            'message': '错误日志添加成功',
            'data': log.to_dict()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'添加错误日志失败: {str(e)}'
        }), 500

@tasks_bp.route('/<string:task_id>/pause', methods=['POST'])
@jwt_required()
def pause_task(task_id):
    """暂停任务"""
    try:
        task = task_service.pause_task(task_id)
        return jsonify({
            'status': 'success',
            'message': f'Task {task_id} pause requested',
            'data': task.to_dict()
        })
    except Exception as e:
        logger.error(f"Error pausing task {task_id}: {e}")
        raise e

@tasks_bp.route('/<string:task_id>/resume', methods=['POST'])
@jwt_required()
def resume_task(task_id):
    """恢复任务"""
    try:
        task = task_service.resume_task(task_id)
        return jsonify({
            'status': 'success',
            'message': f'Task {task_id} resume requested',
            'data': task.to_dict()
        })
    except Exception as e:
        logger.error(f"Error resuming task {task_id}: {e}")
        raise e

@tasks_bp.route('/<string:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """删除任务"""
    try:
        force = request.args.get('force', 'false').lower() == 'true'
        success = task_service.delete_task(task_id, force=force)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Task {task_id} deleted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to delete task {task_id}'
            }), 500
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise e

@tasks_bp.route('/test-connection', methods=['POST'])
@jwt_required()
def test_storage_connection():
    """测试存储连接"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        storage_config = data.get('storage_config')
        if not storage_config:
            raise TaskValidationError("Missing storage_config")
        
        # 创建连接测试任务
        task = task_service.create_connection_test_task(storage_config, user_id)
        
        # 自动启动任务
        started_task = task_service.start_task(task.id)
        
        return jsonify({
            'status': 'success',
            'message': 'Connection test task created and started',
            'data': started_task.to_dict_with_storage_config()
        })
    except Exception as e:
        logger.error(f"Error creating connection test: {e}")
        raise e

@tasks_bp.route('/test-mount', methods=['POST'])
@jwt_required()
def test_mount():
    """测试挂载"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        mount_point = data.get('mount_point')
        storage_config = data.get('storage_config')
        
        if not mount_point:
            raise TaskValidationError("Missing mount_point")
        if not storage_config:
            raise TaskValidationError("Missing storage_config")
        
        # 创建挂载测试任务
        task = task_service.create_mount_test_task(mount_point, storage_config, user_id)
        
        # 自动启动任务
        started_task = task_service.start_task(task.id)
        
        return jsonify({
            'status': 'success',
            'message': 'Mount test task created and started',
            'data': started_task.to_dict_with_storage_config()
        })
    except Exception as e:
        logger.error(f"Error creating mount test: {e}")
        raise e

@tasks_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_task_statistics():
    """获取任务统计信息"""
    try:
        user_id = get_jwt_identity()
        include_all = request.args.get('include_all', 'false').lower() == 'true'
        
        # 如果是管理员用户，可以查看所有统计
        stats_user_id = None if include_all else user_id
        
        stats = task_service.get_task_statistics(stats_user_id)
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting task statistics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@tasks_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_create_tasks():
    """批量创建任务"""
    user_id = get_jwt_identity()
    data = request.get_json()
    tasks_data = data.get('tasks', [])
    
    if not tasks_data:
        return jsonify({
            'status': 'error',
            'message': '任务列表不能为空'
        }), 400
    
    try:
        created_tasks = []
        failed_tasks = []
        
        for task_data in tasks_data:
            try:
                task_data['user_id'] = user_id
                task = task_service.create_task(task_data)
                created_tasks.append(task.to_dict())
            except Exception as e:
                failed_tasks.append({
                    'task_data': task_data,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'批量创建任务完成，成功: {len(created_tasks)}, 失败: {len(failed_tasks)}',
            'data': {
                'created_tasks': created_tasks,
                'failed_tasks': failed_tasks
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'批量创建任务失败: {str(e)}'
        }), 500

@tasks_bp.route('/batch/status', methods=['PUT'])
@jwt_required()
def batch_update_task_status():
    """批量更新任务状态"""
    user_id = get_jwt_identity()
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    status_update = data.get('status_update', {})
    
    if not task_ids or not status_update:
        return jsonify({
            'status': 'error',
            'message': '任务ID列表和状态更新不能为空'
        }), 400
    
    try:
        updated_tasks = []
        failed_tasks = []
        
        for task_id in task_ids:
            try:
                task = Task.query.filter_by(id=task_id, user_id=user_id).first()
                if not task:
                    failed_tasks.append({
                        'task_id': task_id,
                        'error': '任务不存在'
                    })
                    continue
                
                updated_task = task_service.update_task_status(task_id, status_update)
                updated_tasks.append(updated_task.to_dict())
            except Exception as e:
                failed_tasks.append({
                    'task_id': task_id,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'批量更新任务状态完成，成功: {len(updated_tasks)}, 失败: {len(failed_tasks)}',
            'data': {
                'updated_tasks': updated_tasks,
                'failed_tasks': failed_tasks
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'批量更新任务状态失败: {str(e)}'
        }), 500

@tasks_bp.route('/batch/cancel', methods=['PUT'])
@jwt_required()
def batch_cancel_tasks():
    """批量取消任务"""
    user_id = get_jwt_identity()
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({
            'status': 'error',
            'message': '任务ID列表不能为空'
        }), 400
    
    try:
        cancelled_tasks = []
        failed_tasks = []
        
        for task_id in task_ids:
            try:
                task = Task.query.filter_by(id=task_id, user_id=user_id).first()
                if not task:
                    failed_tasks.append({
                        'task_id': task_id,
                        'error': '任务不存在'
                    })
                    continue
                
                cancelled_task = task_service.cancel_task(task_id)
                cancelled_tasks.append(cancelled_task.to_dict())
            except Exception as e:
                failed_tasks.append({
                    'task_id': task_id,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'批量取消任务完成，成功: {len(cancelled_tasks)}, 失败: {len(failed_tasks)}',
            'data': {
                'cancelled_tasks': cancelled_tasks,
                'failed_tasks': failed_tasks
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'批量取消任务失败: {str(e)}'
        }), 500

@tasks_bp.route('/batch/delete', methods=['DELETE'])
@jwt_required()
def batch_delete_tasks():
    """批量删除任务"""
    user_id = get_jwt_identity()
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({
            'status': 'error',
            'message': '任务ID列表不能为空'
        }), 400
    
    try:
        deleted_tasks = []
        failed_tasks = []
        
        for task_id in task_ids:
            try:
                task = Task.query.filter_by(id=task_id, user_id=user_id).first()
                if not task:
                    failed_tasks.append({
                        'task_id': task_id,
                        'error': '任务不存在'
                    })
                    continue
                
                # 只允许删除已完成、失败或取消的任务
                if task.status not in ['completed', 'failed', 'cancelled']:
                    failed_tasks.append({
                        'task_id': task_id,
                        'error': '只能删除已完成、失败或取消的任务'
                    })
                    continue
                
                # 删除任务日志
                TaskLog.query.filter_by(task_id=task_id).delete()
                
                # 删除任务
                db.session.delete(task)
                deleted_tasks.append(task.to_dict())
            except Exception as e:
                failed_tasks.append({
                    'task_id': task_id,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'批量删除任务完成，成功: {len(deleted_tasks)}, 失败: {len(failed_tasks)}',
            'data': {
                'deleted_tasks': deleted_tasks,
                'failed_tasks': failed_tasks
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'批量删除任务失败: {str(e)}'
        }), 500

@tasks_bp.route('/batch/assign', methods=['PUT'])
@jwt_required()
def batch_assign_tasks():
    """批量分配任务到节点"""
    user_id = get_jwt_identity()
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    node_id = data.get('node_id')
    
    if not task_ids or not node_id:
        return jsonify({
            'status': 'error',
            'message': '任务ID列表和节点ID不能为空'
        }), 400
    
    try:
        assigned_tasks = []
        failed_tasks = []
        
        for task_id in task_ids:
            try:
                task = Task.query.filter_by(id=task_id, user_id=user_id).first()
                if not task:
                    failed_tasks.append({
                        'task_id': task_id,
                        'error': '任务不存在'
                    })
                    continue
                
                assigned_task = task_service.assign_task(task_id, node_id)
                assigned_tasks.append(assigned_task.to_dict())
            except Exception as e:
                failed_tasks.append({
                    'task_id': task_id,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'批量分配任务完成，成功: {len(assigned_tasks)}, 失败: {len(failed_tasks)}',
            'data': {
                'assigned_tasks': assigned_tasks,
                'failed_tasks': failed_tasks
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'批量分配任务失败: {str(e)}'
        }), 500

@tasks_bp.route('/batch/retry', methods=['PUT'])
@jwt_required()
def batch_retry_tasks():
    """批量重试任务"""
    user_id = get_jwt_identity()
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({
            'status': 'error',
            'message': '任务ID列表不能为空'
        }), 400
    
    try:
        retried_tasks = []
        failed_tasks = []
        
        for task_id in task_ids:
            try:
                task = Task.query.filter_by(id=task_id, user_id=user_id).first()
                if not task:
                    failed_tasks.append({
                        'task_id': task_id,
                        'error': '任务不存在'
                    })
                    continue
                
                retried_task = task_service.retry_task(task_id)
                retried_tasks.append(retried_task.to_dict())
            except Exception as e:
                failed_tasks.append({
                    'task_id': task_id,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'批量重试任务完成，成功: {len(retried_tasks)}, 失败: {len(failed_tasks)}',
            'data': {
                'retried_tasks': retried_tasks,
                'failed_tasks': failed_tasks
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'批量重试任务失败: {str(e)}'
        }), 500