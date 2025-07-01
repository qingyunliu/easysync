import logging
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from . import nodes_bp
from backend import db
from backend.app.models import Node, AuditLog
from backend.app.utils.ssh_utils import SSHClient
from backend.app.utils import utils
from .service import NodeService
from .errors import NodeError, NodeNotFoundError, NodeUnhealthyError, NodeOperationError

node_service = NodeService()

@nodes_bp.errorhandler(NodeError)
def handle_node_error(error):
    """处理节点错误"""
    if isinstance(error, NodeNotFoundError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 404
    elif isinstance(error, NodeUnhealthyError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 503
    elif isinstance(error, NodeOperationError):
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
    else:
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 500

@nodes_bp.route('', methods=['POST'])
@jwt_required()
def create_node():
    """创建节点"""
    data = request.get_json()
    name = data.get('name')
    ipaddress = data.get('ipaddress')
    username = data.get('username')
    auth_type = data.get('auth_type')
    password = data.get('password')
    ssh_key = data.get('ssh_key')
    port = data.get('port')
    user_id = get_jwt_identity()

    node = Node(name=name,
                ipaddress=ipaddress,
                username=username,
                auth_type=auth_type,
                password=password,
                auth_key=ssh_key,
                port=port,
                user_id=user_id)
    db.session.add(node)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': '节点创建成功',
        'data': node.to_dict()
    }), 201

@nodes_bp.route('', methods=['GET'])
@jwt_required()
def get_nodes():
    """获取节点列表"""
    current_user_id = get_jwt_identity()
    nodes = Node.query.filter_by(user_id=current_user_id).all()
    return jsonify({
        'status': 'success',
        'message': '节点列表获取成功',
        'data': [node.to_dict() for node in nodes]
    })

@nodes_bp.route('/<string:node_id>/test-connection', methods=['POST'])
@jwt_required()
def test_connection(node_id):
    try:
        node = Node.query.get_or_404(node_id)
        if str(node.user_id) != get_jwt_identity():
            return jsonify({'error': '无权访问此服务器'}), 403

        # 测试SSH连接
        with SSHClient(node) as ssh:
            # 连接成功即可
            node.status = 'online'
            node.last_seen = datetime.utcnow()
            db.session.commit()
            
            # 记录审计日志
            audit_log = AuditLog(
                user_id=node.user_id,
                action='test_connection',
                resource_type='node',
                resource_id=node.id,
                details={'status': 'success'}
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': '连接测试成功'
            }), 200
            
    except Exception as e:
        # 更新状态为离线
        node.status = 'offline'
        db.session.commit()
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=node.user_id,
            action='test_connection',
            resource_type='node',
            resource_id=node.id,
            details={'status': 'failed', 'error': str(e)}
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 400

@nodes_bp.route('/<string:node_id>/detail', methods=['GET'])
def get_node_detail(node_id):
    try:
        node = Node.query.get_or_404(node_id)
        
        with SSHClient(node=node) as ssh:
            # 获取系统信息
            stdout, stderr, exit_code = ssh.execute_command('cat /etc/os-release')
            os_info = stdout
            os_type = utils.parse_os_info(os_info)
            
            # 获取CPU信息
            stdout, stderr, exit_code = ssh.execute_command('lscpu')
            cpu_info = utils.parse_cpu_info(stdout)
            
            # 获取内存信息
            stdout, stderr, exit_code = ssh.execute_command('free -b')
            memory_info = utils.parse_memory_info(stdout)
            
            # 获取磁盘信息
            stdout, stderr, exit_code = ssh.execute_command('df -B1')
            disk_info = utils.parse_disk_info(stdout)
            
            # 获取网络信息
            stdout, stderr, exit_code = ssh.execute_command('ip addr')
            network_info = utils.parse_network_info(stdout)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'os_type': os_type,
                    'cpu_info': cpu_info,
                    'memory_info': memory_info,
                    'disk_info': disk_info,
                    'network_info': network_info
                }
            })
            
    except Exception as e:
        logging.error(f"获取主机详情失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取主机详情失败'
        }), 500

@nodes_bp.route('/<string:node_id>', methods=['GET'])
@jwt_required()
def get_node(node_id):
    """获取节点详情"""
    current_user_id = get_jwt_identity()
    node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()
    if not node:
        return jsonify({
            'status': 'error',
            'message': '节点不存在'
        }), 404
    return jsonify({
        'status': 'success',
        'message': '节点详情获取成功',
        'data': node.to_dict()
    })

@nodes_bp.route('/<string:node_id>', methods=['PUT'])
@jwt_required()
def update_node(node_id):
    """更新节点"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get('name')
    host = data.get('host')
    port = data.get('port')
    type = data.get('type')
    config = data.get('config', {})

    node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()
    if not node:
        return jsonify({
            'status': 'error',
            'message': '节点不存在'
        }), 404

    if name:
        node.name = name
    if host:
        node.host = host
    if port:
        node.port = port
    if type:
        node.type = type
    if config:
        node.config = config

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': '节点更新成功',
        'data': node.to_dict()
    })

@nodes_bp.route('/<string:node_id>', methods=['DELETE'])
@jwt_required()
def delete_node(node_id):
    """删除节点"""
    current_user_id = get_jwt_identity()
    node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()
    if not node:
        return jsonify({
            'status': 'error',
            'message': '节点不存在'
        }), 404

    db.session.delete(node)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': '节点删除成功'
    })

@nodes_bp.route('/register', methods=['POST'])
def register_node():
    """注册节点"""
    data = request.get_json()
    name = data.get('name')
    version = data.get('version')
    host = data.get('host')
    system_info = data.get('system_info', {})
    
    # 创建节点
    node = Node(
        name=name,
        host=host,
        port=0,  # 端口由节点自行管理
        status='active',
        version=version,
        config={},
        system_info=system_info
    )
    
    db.session.add(node)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '节点注册成功',
        'data': {
            'node_id': node.id
        }
    }), 201

@nodes_bp.route('/<string:node_id>/heartbeat', methods=['POST'])
def heartbeat(node_id):
    """节点心跳"""
    data = request.get_json()
    system_info = data.get('system_info', {})
    
    try:
        node_service.update_node_heartbeat(node_id, system_info)
        return jsonify({
            'status': 'success',
            'message': '心跳更新成功'
        })
    except NodeNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404

@nodes_bp.route('/<string:node_id>/tasks', methods=['GET'])
def get_node_tasks(node_id):
    """获取节点待执行的任务"""
    try:
        tasks = node_service.get_node_tasks(node_id)
        return jsonify({
            'status': 'success',
            'message': '获取任务成功',
            'data': tasks
        })
    except NodeNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except NodeUnhealthyError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 503

@nodes_bp.route('/<string:node_id>/tasks/<string:task_id>/status', methods=['PUT'])
def update_task_status(node_id, task_id):
    """更新任务状态"""
    data = request.get_json()
    status = data.get('status', {})
    
    try:
        node_service.update_task_status(node_id, task_id, status)
        return jsonify({
            'status': 'success',
            'message': '任务状态更新成功'
        })
    except NodeNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except NodeOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@nodes_bp.route('/<string:node_id>/storage/mount', methods=['POST'])
def mount_storage(node_id):
    """挂载存储"""
    data = request.get_json()
    storage_config = data.get('storage_config', {})
    
    try:
        node_service.mount_storage(node_id, storage_config)
        return jsonify({
            'status': 'success',
            'message': '存储挂载成功'
        })
    except NodeNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except NodeOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@nodes_bp.route('/<string:node_id>/storage/unmount', methods=['POST'])
def unmount_storage(node_id):
    """卸载存储"""
    data = request.get_json()
    mount_point = data.get('mount_point')
    
    try:
        node_service.unmount_storage(node_id, mount_point)
        return jsonify({
            'status': 'success',
            'message': '存储卸载成功'
        })
    except NodeNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except NodeOperationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400