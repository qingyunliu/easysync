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
    """获取任务详情"""
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
        'data': task.to_dict()
    })

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """创建任务"""
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
    """获取节点任务"""
    try:
        tasks = task_service.get_node_tasks(node_id)
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

@tasks_bp.route('/<string:task_id>/logs', methods=['GET'])
@jwt_required()
def get_task_logs(task_id):
    """获取任务日志"""
    user_id = get_jwt_identity()
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

@tasks_bp.route('/<string:task_id>/run', methods=['POST'])
@jwt_required()
def run_task(task_id):
    """立即运行任务"""
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    # 创建临时调度
    schedule = TaskSchedule(
        task_id=task.id,
        schedule_type='once',
        schedule_time=datetime.utcnow().isoformat()
    )
    
    # 运行任务
    scheduler.add_task(task, schedule)
    
    return jsonify({
        'id': task.id,
        'status': 'running'
    })

@tasks_bp.route('/<string:task_id>/status', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """获取任务运行状态"""
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    status = scheduler.get_task_status(task.id)
    return jsonify(status)

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

@tasks_bp.route('/<string:task_id>/schedule', methods=['POST'])
@jwt_required()
def schedule_task(task_id):
    """调度任务"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user_id:
        return jsonify({'error': '任务不属于当前用户'}), 403
    scheduler_service = SchedulerService()
    scheduler_service.schedule_task(task_id, request.json)
    return jsonify({
        'status': 'success',
        'message': '任务已调度'
    })

@tasks_bp.route('/<string:task_id>/unschedule', methods=['POST'])
@jwt_required()
def unschedule_task(task_id):
    """取消任务调度"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user_id:
        return jsonify({'error': '任务不属于当前用户'}), 403
    scheduler_service = SchedulerService()
    scheduler_service.unschedule_task(task_id)
    return jsonify({
        'status': 'success',
        'message': '任务调度已取消'
    })

@tasks_bp.route('/<string:task_id>/start', methods=['POST'])
@jwt_required()
def start_task(task_id):
    """启动任务"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user_id:
        return jsonify({'error': '任务不属于当前用户'}), 403
    scheduler_service = SchedulerService()
    if scheduler_service.start_task(task_id):
        return jsonify({
            'status': 'success',
            'message': '任务已启动'
        })
    return jsonify({
        'status': 'error',
        'message': '任务启动失败'
    }), 500

@tasks_bp.route('/<string:task_id>/stop', methods=['POST'])
@jwt_required()
def stop_task(task_id):
    """停止任务"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user_id:
        return jsonify({'error': '任务不属于当前用户'}), 403
    scheduler_service = SchedulerService()
    if scheduler_service.stop_task(task_id):
        return jsonify({
            'status': 'success',
            'message': '任务已停止'
        })
    return jsonify({
        'status': 'error',
        'message': '任务停止失败'
    }), 500