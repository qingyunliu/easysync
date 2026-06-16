from flask import jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models import Task, TaskLog
from . import tasks_bp
from .service import TaskService
import logging
from datetime import datetime
from .errors import TaskError, TaskNotFoundError, TaskOperationError, TaskValidationError, TaskStateError
from backend.app.auth.services import AuditService
from backend.app.notifications.services import NotificationService
from backend.app.events.middleware import record_api_event

logger = logging.getLogger(__name__)

task_service = TaskService()
notification_service = NotificationService()

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
@record_api_event('task', 'create')
def create_task():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # 验证必需字段
        name = data.get('name')
        type = data.get('type')
        
        if not all([name, type]):
            AuditService.log_task_operation(
                user_id=user_id,
                action='create',
                task_id=None,
                task_name=name,
                details={'error': '名称和类型不能为空'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '名称和类型不能为空'
            }), 400

        # 构建任务数据，包含所有前端传递的字段
        task_data = {
            'name': name,
            'description': data.get('description', ''),
            'type': type,
            'priority': data.get('priority',2),
            'user_id': user_id,
            'node_id': data.get('node_id'),
            'source_type': data.get('source_type'),
            'source_client_id': data.get('source_client_id'),
            'source_storage_id': data.get('source_storage_id'),
            'source_path': data.get('source_path'),
            'target_storage_id': data.get('target_storage_id'),
            'target_path': data.get('target_path'),
            'options': data.get('options', {}),
            'auto_start': data.get('auto_start', False)  # 自动启动选项
        }
            
        task = task_service.create_task(task_data)
        
        # 发送任务创建通知
        notification_service.create_notification(
            user_id=user_id,
            type='task_created',
            title=f'任务已创建: {task.name}',
            content=f'同步任务 {task.name} 已成功创建，等待执行。',
            level='info'
        )
        
        AuditService.log_task_operation(
            user_id=user_id,
            action='create',
            task_id=task.id,
            task_name=task.name,
            details={'msg': '任务创建成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '任务创建成功',
            'task': task.to_dict()
        }), 201
    except ValueError as e:
        AuditService.log_task_operation(
            user_id=user_id,
            action='create',
            task_id=None,
            task_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        AuditService.log_task_operation(
            user_id=user_id,
            action='create',
            task_id=None,
            task_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'创建任务失败: {str(e)}'
        }), 500

@tasks_bp.route('/<string:task_id>/status', methods=['PUT'])
@jwt_required()
@record_api_event('task', 'update_status')
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
@record_api_event('task', 'cancel')
def cancel_task(task_id):
    """取消任务"""
    user_id = get_jwt_identity()
    
    try:
        task = task_service.cancel_task(task_id)
        # 发送任务取消通知
        notification_service.notify_task_cancelled(
            user_id=user_id,
            task_name=task.name,
            reason='用户手动取消'
        )
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
@record_api_event('task', 'retry')
def retry_task(task_id):
    """重试任务"""
    user_id = get_jwt_identity()
    
    try:
        task = task_service.retry_task(task_id)
        # 发送任务重试通知
        notification_service.notify_task_retry(
            user_id=user_id,
            task_name=task.name,
            retry_count=task.retry_count or 1,
            max_retries=3
        )
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
        # 发送任务启动通知
        notification_service.notify_task_started(
            user_id=current_user_id,
            task_name=task.name
        )
        return jsonify({
            'status': 'success',
            'message': '任务已启动'
        })
    return jsonify({
        'status': 'error',
        'message': '任务启动失败'
    }), 500

@tasks_bp.route('/<string:task_id>/restart', methods=['POST'])
@jwt_required()
def restart_task(task_id):
    """重新运行已完成任务"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user_id:
        return jsonify({'error': '任务不属于当前用户'}), 403
    
    try:
        # 重置任务状态
        task.status = 'pending'
        task.progress = 0
        task.error = None
        task.started_at = None
        task.completed_at = None
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 启动任务
        if task_service.start_task(task_id):
            # 发送任务启动通知
            notification_service.notify_task_started(
                user_id=current_user_id,
                task_name=task.name
            )
            return jsonify({
                'status': 'success',
                'message': '任务重新运行成功'
            })
        return jsonify({
            'status': 'error',
            'message': '任务重新运行失败'
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'重新运行失败: {str(e)}'
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
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status_filter = request.args.get('status', '')
        latest_progress_only = request.args.get('latest_progress_only', 'true').lower() == 'true'
        
        # 构建查询
        query = TaskLog.query.filter(TaskLog.task_id == task_id)
        
        # 状态过滤
        if status_filter:
            query = query.filter(TaskLog.status == status_filter)
        
        # 如果只显示最新进度日志
        if latest_progress_only:
            # 获取最新的进度日志
            latest_progress = TaskLog.query.filter(
                TaskLog.task_id == task_id,
                TaskLog.message.like('%同步进度%')
            ).order_by(TaskLog.created_at.desc()).first()
            
            # 获取其他类型的日志
            other_logs = TaskLog.query.filter(
                TaskLog.task_id == task_id,
                ~TaskLog.message.like('%同步进度%')
            ).order_by(TaskLog.created_at.desc())
            
            # 合并结果
            all_logs = []
            if latest_progress:
                all_logs.append(latest_progress)
            all_logs.extend(other_logs.all())
            
            # 手动分页
            start = (page - 1) * per_page
            end = start + per_page
            paginated_logs = all_logs[start:end]
            total = len(all_logs)
        else:
            # 正常分页查询
            pagination = query.order_by(TaskLog.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            paginated_logs = pagination.items
            total = pagination.total
        
        return jsonify({
            'status': 'success',
            'message': '任务日志获取成功',
            'data': [log.to_dict() for log in paginated_logs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
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
        # 发送任务暂停通知
        notification_service.notify_task_paused(
            user_id=task.user_id,
            task_name=task.name,
            reason='用户手动暂停'
        )
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
        # 发送任务恢复通知
        notification_service.notify_task_resumed(
            user_id=task.user_id,
            task_name=task.name
        )
        return jsonify({
            'status': 'success',
            'message': f'Task {task_id} resume requested',
            'data': task.to_dict()
        })
    except Exception as e:
        logger.error(f"Error resuming task {task_id}: {e}")
        raise e

@tasks_bp.route('/<string:task_id>/stop', methods=['POST'])
@jwt_required()
def stop_task(task_id):
    """停止任务"""
    try:
        task = task_service.stop_task(task_id)
        # 发送任务停止通知
        notification_service.notify_task_stopped(
            user_id=task.user_id,
            task_name=task.name,
            reason='用户手动停止'
        )
        return jsonify({
            'status': 'success',
            'message': f'Task {task_id} stopped',
            'data': task.to_dict()
        })
    except Exception as e:
        logger.error(f"Error stopping task {task_id}: {e}")
        raise e

@tasks_bp.route('/<string:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    try:
        data = request.get_json()
        name = data.get('name')
        status = data.get('status')
        progress = data.get('progress')
        result = data.get('result')
        user_id = get_jwt_identity()
        
        task = task_service.update_task(task_id, name, status, progress, result)
        if not task:
            AuditService.log_task_operation(
                user_id=user_id,
                action='update',
                task_id=task_id,
                task_name=name,
                details={'error': '任务不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404
        AuditService.log_task_operation(
            user_id=user_id,
            action='update',
            task_id=task.id,
            task_name=task.name,
            details={'msg': '任务更新成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '任务更新成功',
            'task': task.to_dict()
        })
    except ValueError as e:
        AuditService.log_task_operation(
            user_id=user_id,
            action='update',
            task_id=task_id,
            task_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        AuditService.log_task_operation(
            user_id=user_id,
            action='update',
            task_id=task_id,
            task_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'更新任务失败: {str(e)}'
        }), 500

@tasks_bp.route('/<string:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    try:
        task = Task.query.get_or_404(task_id)
        if task.user_id != user_id:
            return jsonify({'error': '任务不属于当前用户'}), 403
            
        if not task_service.delete_task(task_id):
            AuditService.log_task_operation(
                user_id=user_id,
                action='delete',
                task_id=task_id,
                task_name=None,
                details={'error': '任务不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404
            
        # 发送任务删除通知
        notification_service.create_notification(
            user_id=user_id,
            type='task_deleted',
            title=f'任务已删除: {task.name}',
            content=f'同步任务 {task.name} 已被删除。',
            level='info'
        )
        
        AuditService.log_task_operation(
            user_id=user_id,
            action='delete',
            task_id=task_id,
            task_name=None,
            details={'msg': '任务删除成功'},
            result='success'
        )
        return '', 204
    except Exception as e:
        AuditService.log_task_operation(
            user_id=user_id,
            action='delete',
            task_id=task_id,
            task_name=None,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'删除任务失败: {str(e)}'
        }), 500

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

@tasks_bp.route('/<string:task_id>/logs/cleanup', methods=['POST'])
@jwt_required()
def cleanup_task_logs(task_id):
    """清理任务日志"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    try:
        # 验证任务是否存在且属于当前用户
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return jsonify({
                'status': 'error',
                'message': '任务不存在'
            }), 404

        cleanup_type = data.get('type', 'old')  # 'old' 或 'duplicate'
        days = data.get('days', 7)
        
        if cleanup_type == 'old':
            deleted_count = task_service.cleanup_old_progress_logs(task_id, days)
            message = f"清理了 {deleted_count} 条过期的进度日志"
        elif cleanup_type == 'duplicate':
            deleted_count = task_service.cleanup_duplicate_progress_logs(task_id)
            message = f"清理了 {deleted_count} 条重复的进度日志"
        else:
            return jsonify({
                'status': 'error',
                'message': '无效的清理类型'
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': {'deleted_count': deleted_count}
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'清理日志失败: {str(e)}'
        }), 500

@tasks_bp.route('/logs/cleanup', methods=['POST'])
@jwt_required()
def cleanup_all_task_logs():
    """全局清理任务日志"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    try:
        cleanup_type = data.get('type', 'old')  # 'old' 或 'duplicate'
        days = data.get('days', 7)
        
        if cleanup_type == 'old':
            deleted_count = task_service.cleanup_old_progress_logs(days=days)
            message = f"清理了 {deleted_count} 条过期的进度日志"
        elif cleanup_type == 'duplicate':
            deleted_count = task_service.cleanup_all_duplicate_progress_logs()
            message = f"清理了 {deleted_count} 条重复的进度日志"
        else:
            return jsonify({
                'status': 'error',
                'message': '无效的清理类型'
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': {'deleted_count': deleted_count}
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'清理日志失败: {str(e)}'
        }), 500