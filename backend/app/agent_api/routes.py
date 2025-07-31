from flask import Blueprint, request, jsonify, current_app
from backend import db
from backend.app.models import Node, Task, MonitorData
from backend.app.commands.service import RealTimeCommandService
from backend.app.storages.services import StorageRealTimeService
from . import agent_bp
from werkzeug.security import gen_salt
from functools import wraps
import datetime

# 实时命令服务实例
command_service = RealTimeCommandService()
storage_realtime_service = StorageRealTimeService()

# 简单token生成与校验（可替换为更安全实现）
def generate_token():
    return gen_salt(32)

def agent_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        node_id = kwargs.get('node_id')
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        node = Node.query.filter_by(id=node_id).first()
        if not node or not node.config or node.config.get('agent_token') != token:
            return jsonify({'status': 'error', 'message': '无效token或节点'}), 401
        return f(*args, **kwargs)
    return decorated

# 1. 注册节点
@agent_bp.route('/register', methods=['POST'])
def agent_register():
    data = request.get_json()
    name = data.get('name')
    hostname = data.get('hostname')
    ipaddress = data.get('ipaddress')
    version = data.get('version')
    user_id = data.get('user_id') or 1  # 默认用户ID为1
    node_id = data.get('node_id')
    system_info = data.get('system_info', {})

    existing_node = Node.query.filter_by(id=node_id).first()
    if existing_node:
        token = existing_node.config.get('agent_token') if existing_node.config else generate_token()
        current_app.logger.debug(f"Found existing node({node_id}), token: {token}")
        if not existing_node.config or not existing_node.config.get('agent_token'):
            current_app.logger.debug(f"No token found for node({node_id}), generating new token")
            token = generate_token()
            existing_node.config = existing_node.config or {}
            existing_node.config['agent_token'] = token
            db.session.commit()
        
        # 更新节点状态为在线
        existing_node.status = 'online'
        existing_node.last_heartbeat = datetime.datetime.utcnow()
        db.session.commit()

        current_app.logger.debug(f"Updated node({node_id}) status to online")
        
        return jsonify({
            'status': 'success', 
            'message': '节点已注册，直接返回', 
            'data': {
                'id': existing_node.id,
                'user_id': existing_node.user_id,
                'token': token
            }
        })

    # 未注册，创建新节点
    token = generate_token()
    node = Node(
        name=name, 
        hostname=hostname,
        ipaddress=ipaddress, 
        port=22, 
        status='online',  # 新注册的节点状态为在线
        username="", 
        password="",
        user_id=user_id,
        config={'agent_token': token}, 
        system_info=system_info,
        last_heartbeat=datetime.datetime.utcnow()
    )
    db.session.add(node)
    db.session.commit()
    current_app.logger.debug(f"Created new node({node.id}), token: {token}")
    return jsonify({
        'status': 'success', 
        'message': '注册成功', 
        'data': {
            'id': node.id, 
            'user_id': node.user_id,
            'token': token
        }
    })

# 2. 心跳
@agent_bp.route('/<string:node_id>/heartbeat', methods=['POST'])
@agent_token_required
def agent_heartbeat(node_id):
    try:
        data = request.get_json() or {}
        node = Node.query.get(node_id)
        
        if not node:
            return jsonify({'status': 'error', 'message': '节点不存在'}), 404
        
        # 更新心跳时间和状态
        node.last_heartbeat = datetime.datetime.utcnow()
        node.status = 'online'
        
        # 更新Agent状态，默认为running
        agent_status = data.get('agent_status', 'running')
        if agent_status in ['running', 'active', 'inactive', 'error']:
            node.agent_status = agent_status
        else:
            node.agent_status = 'running'  # 默认状态
            
        # 更新系统信息
        if 'system_info' in data:
            node.system_info = data['system_info']
            
        # 更新Agent版本信息
        if 'version' in data:
            node.agent_version = data['version']
            
        current_app.logger.debug(f"节点 {node_id} ({node.name}) 心跳更新: status={node.status}, agent_status={node.agent_status}")
        
        db.session.commit()
        return jsonify({
            'status': 'success', 
            'message': '心跳成功',
            'node_status': node.status,
            'agent_status': node.agent_status
        })
        
    except Exception as e:
        current_app.logger.error(f"处理节点 {node_id} 心跳失败: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': '心跳处理失败'}), 500

# 3. 拉取任务（包含存储配置信息）
@agent_bp.route('/<string:node_id>/tasks', methods=['GET'])
@agent_token_required
def agent_get_tasks(node_id):
    # 获取分配给此节点的任务，包括所有需要处理的状态
    tasks = Task.query.filter_by(node_id=node_id).filter(
        Task.status.in_([
            'assigned',           # 新分配的任务
            'running',           # 运行中的任务
            'cancel_requested',  # 取消请求
            'pause_requested',   # 暂停请求
            'resume_requested'   # 恢复请求
        ])
    ).all()
    
    # 确保返回完整的任务信息，包括存储配置
    task_data = []
    for task in tasks:
        task_dict = task.to_dict_with_storage_config()
        
        # 为特殊任务类型添加额外信息
        if task.type == 'test-connection':
            task_dict['storage_config'] = task.options.get('storage_config', {})
        elif task.type == 'mount-check':
            task_dict['mount_point'] = task.source_path
            task_dict['storage_config'] = task.options.get('storage_config', {})
        
        task_data.append(task_dict)
    return jsonify({
        'status': 'success', 
        'data': task_data
    })

# 4. 获取单个任务详情（包含存储配置）
@agent_bp.route('/<string:node_id>/tasks/<string:task_id>', methods=['GET'])
@agent_token_required
def agent_get_task_detail(node_id, task_id):
    task = Task.query.filter_by(id=task_id, node_id=node_id).first()
    if not task:
        return jsonify({'status': 'error', 'message': '任务不存在或不属于该节点'}), 404
    
    return jsonify({
        'status': 'success',
        'data': task.to_dict_with_storage_config()
    })

# 5. 上报任务状态
@agent_bp.route('/<string:node_id>/tasks/<string:task_id>/status', methods=['PUT'])
@agent_token_required
def agent_update_task_status(node_id, task_id):
    data = request.get_json()
    task = Task.query.get(task_id)
    if not task or task.node_id != node_id:
        return jsonify({'status': 'error', 'message': '任务不存在或不属于该节点'}), 404
    
    # 更新任务状态
    task.status = data.get('status', task.status)
    task.progress = data.get('progress', task.progress)
    task.error = data.get('error', task.error)
    task.updated_at = datetime.datetime.utcnow()
    
    # 支持details字段
    if 'details' in data:
        task.details = data['details']
    
    # 处理任务完成时间
    if task.status in ['completed', 'failed', 'cancelled']:
        task.completed_at = datetime.datetime.utcnow()
    elif task.status == 'running' and not task.started_at:
        task.started_at = datetime.datetime.utcnow()
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': '任务状态已更新'})

# 6. 上报任务进度日志
@agent_bp.route('/<string:node_id>/tasks/<string:task_id>/logs', methods=['POST'])
@agent_token_required
def agent_report_task_log(node_id, task_id):
    data = request.get_json()
    task = Task.query.filter_by(id=task_id, node_id=node_id).first()
    if not task:
        return jsonify({'status': 'error', 'message': '任务不存在或不属于该节点'}), 404
    
    # 创建任务日志
    from backend.app.models.task import TaskLog
    log = TaskLog(
        task_id=task_id,
        user_id=task.user_id,
        status=data.get('status', 'info'),
        message=data.get('message', ''),
        details=data.get('details', {})
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '任务日志已记录'})

# 7. 测试存储连接
@agent_bp.route('/<string:node_id>/storage/<string:storage_id>/test', methods=['POST'])
@agent_token_required
def agent_test_storage_connection(node_id, storage_id):
    from backend.app.models.storage import Storage
    
    storage = Storage.query.get(storage_id)
    if not storage:
        return jsonify({'status': 'error', 'message': '存储不存在'}), 404
    
    # 返回存储配置供Agent测试
    return jsonify({
        'status': 'success',
        'data': {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            }
        }
    })

# 8. 上报监控
@agent_bp.route('/<string:node_id>/metrics', methods=['POST'])
@agent_token_required
def agent_report_metrics(node_id):
    data = request.get_json()
    node = Node.query.get(node_id)
    metrics = data.get('metrics', {})
    node.system_info = metrics
    db.session.commit()
    try:
        MonitorData.create_monitor_data(
            user_id=node.user_id,
            node_id=node.id,
            data=metrics
        )
        current_app.logger.info(f"Received node({node_id}) metrics: {metrics}")
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'监控数据写入失败: {e}'})
    return jsonify({'status': 'success', 'message': '监控数据已上报'})

# 6. 上报错误
@agent_bp.route('/<string:node_id>/errors', methods=['POST'])
@agent_token_required
def agent_report_error(node_id):
    data = request.get_json()
    # 可扩展为写入专门的错误表
    current_app.logger.error(f'Agent节点{node_id}错误: {data}')
    return jsonify({'status': 'success', 'message': '错误已上报'})

# 7. 上报告警
@agent_bp.route('/<string:node_id>/alerts', methods=['POST'])
@agent_token_required
def agent_send_alert(node_id):
    data = request.get_json()
    node = Node.query.get(node_id)
    if not node:
        return jsonify({'status': 'error', 'message': '节点不存在'}), 404
    
    try:
        # 创建告警记录
        from backend.app.models.alert import Alert
        alert = Alert(
            node_id=node_id,
            user_id=node.user_id,
            alert_type=data.get('alert_type'),
            level=data.get('level', 'warning'),
            message=data.get('message'),
            value=data.get('value'),
            threshold=data.get('threshold'),
            timestamp=datetime.datetime.fromisoformat(data.get('timestamp', datetime.datetime.utcnow().isoformat())),
            status='active'
        )
        db.session.add(alert)
        db.session.commit()
        
        # 记录日志
        current_app.logger.warning(f'Alert from node {node_id}: {data.get("message")}')
        
        return jsonify({'status': 'success', 'message': '告警已接收'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to save alert: {e}')
        return jsonify({'status': 'error', 'message': f'告警保存失败: {e}'}), 500 

@agent_bp.route('/<string:node_id>/commands', methods=['GET'])
@agent_token_required
def get_pending_commands(node_id):
    """Agent获取待执行的实时命令"""
    try:
        # 验证节点权限（可以加入token验证）
        commands = command_service.get_pending_commands(node_id)
        current_app.logger.info(f"Received node({node_id}) pending commands: {commands}")
        return jsonify({
            'status': 'success',
            'data': commands
        })
    except Exception as e:
        current_app.logger.error(f"获取待执行命令失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取命令失败: {str(e)}'
        }), 500


@agent_bp.route('/<string:node_id>/commands/<string:command_id>/status', methods=['PUT'])
@agent_token_required
def update_command_status(node_id, command_id):
    """Agent更新命令执行状态"""
    try:
        status_data = request.get_json()
        current_app.logger.info(f"Received node({node_id}) command({command_id}) status update: {status_data}")
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
        current_app.logger.error(f"更新命令状态失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'更新状态失败: {str(e)}'
        }), 500