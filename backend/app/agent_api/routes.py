from flask import Blueprint, request, jsonify, current_app
from backend import db
from backend.app.models import Node, Task, MonitorData
from . import agent_bp
from werkzeug.security import gen_salt
from functools import wraps
import datetime

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
    ipaddress = data.get('ipaddress')
    version = data.get('version')
    user_id = data.get('user_id')
    system_info = data.get('system_info', {})

    # 先查找是否已注册（根据IP地址和用户ID判断）
    existing_node = Node.query.filter_by(ipaddress=ipaddress, user_id=user_id).first()
    if existing_node:
        # 已注册，直接返回原有信息
        token = existing_node.config.get('agent_token') if existing_node.config else generate_token()
        # 如果老节点没有token，补发一个
        if not existing_node.config or not existing_node.config.get('agent_token'):
            token = generate_token()
            existing_node.config = existing_node.config or {}
            existing_node.config['agent_token'] = token
            db.session.commit()
        
        # 更新节点状态为在线
        existing_node.status = 'online'
        existing_node.last_heartbeat = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': '节点已注册，直接返回', 
            'data': {'node_id': existing_node.id, 'token': token}
        })

    # 未注册，创建新节点
    token = generate_token()
    node = Node(
        name=name, 
        ipaddress=ipaddress, 
        port=0, 
        status='active', 
        username="", 
        password="",
        user_id=user_id,
        config={'agent_token': token}, 
        system_info=system_info
    )
    db.session.add(node)
    db.session.commit()
    return jsonify({
        'status': 'success', 
        'message': '注册成功', 
        'data': {'node_id': node.id, 'token': token}
    })

# 2. 心跳
@agent_bp.route('/<string:node_id>/heartbeat', methods=['POST'])
@agent_token_required
def agent_heartbeat(node_id):
    data = request.get_json()
    node = Node.query.get(node_id)
    node.last_heartbeat = datetime.datetime.utcnow()
    node.status = 'online'
    node.system_info = data.get('system_info', {})
    db.session.commit()
    return jsonify({'status': 'success', 'message': '心跳成功'})

# 3. 拉取任务
@agent_bp.route('/<string:node_id>/tasks', methods=['GET'])
@agent_token_required
def agent_get_tasks(node_id):
    tasks = Task.query.filter_by(node_id=node_id, status='pending').all()
    return jsonify({'status': 'success', 'data': [t.to_dict() for t in tasks]})

# 4. 上报任务状态
@agent_bp.route('/<string:node_id>/tasks/<string:task_id>/status', methods=['PUT'])
@agent_token_required
def agent_update_task_status(node_id, task_id):
    data = request.get_json()
    task = Task.query.get(task_id)
    if not task or task.node_id != node_id:
        return jsonify({'status': 'error', 'message': '任务不存在或不属于该节点'}), 404
    task.status = data.get('status', task.status)
    task.progress = data.get('progress', task.progress)
    task.error = data.get('error', task.error)
    task.updated_at = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success', 'message': '任务状态已更新'})

# 5. 上报监控
@agent_bp.route('/<string:node_id>/metrics', methods=['POST'])
@agent_token_required
def agent_report_metrics(node_id):
    data = request.get_json()
    node = Node.query.get(node_id)
    metrics = data.get('metrics', {})
    node.system_info = metrics
    db.session.commit()
    # 新增：写入历史监控表
    try:
        MonitorData.create_monitor_data(
            user_id=node.user_id,
            node_id=node.id,
            data=metrics
        )
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