import os
import logging
from datetime import datetime
from flask import request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.models import Node, AuditLog, MonitorData
from backend.app.utils.ssh_utils import SSHClient
from backend.app.utils import utils
from . import nodes_bp
from .status_monitor import get_status_monitor
from .service import NodeService
from .errors import NodeError, NodeNotFoundError, NodeUnhealthyError, NodeOperationError
from backend.app.auth.services import AuditService
from backend.app.notifications.services import NotificationService
from backend.app.events.middleware import record_agent_event

logger = logging.getLogger(__name__)

node_service = NodeService()
notification_service = NotificationService()

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
@record_agent_event('create')
def create_node():
    """创建节点"""
    try:
        data = request.get_json()
        name = data.get('name')
        ipaddress = data.get('ipaddress')
        username = data.get('username')
        auth_type = data.get('auth_type')
        password = data.get('password')
        ssh_key = data.get('ssh_key')
        port = data.get('port')
        group = data.get('group', 'default')
        tags = data.get('tags', '')
        user_id = get_jwt_identity()

        if not all([name, ipaddress, username]):
            AuditService.log_node_operation(
                user_id=user_id,
                action='create',
                node_id=None,
                node_name=name,
                details={'error': '缺少必要字段'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '缺少必要字段'
            }), 400

        node = Node(name=name,
                    ipaddress=ipaddress,
                    username=username,
                    auth_type=auth_type,
                    password=password,
                    auth_key=ssh_key,
                    port=port,
                    group=group,
                    tags=tags,
                    user_id=user_id)
        db.session.add(node)
        db.session.commit()
        
        # 发送节点创建通知
        notification_service.create_notification(
            user_id=user_id,
            type='node_created',
            title=f'节点已创建: {node.name}',
            content=f'节点 {node.name} ({ipaddress}) 已成功创建。',
            level='success'
        )
        
        AuditService.log_node_operation(
            user_id=user_id,
            action='create',
            node_id=node.id,
            node_name=node.name,
            details={'msg': '节点创建成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '节点创建成功',
            'data': node.to_dict()
        }), 201
    except Exception as e:
        AuditService.log_node_operation(
            user_id=user_id,
            action='create',
            node_id=None,
            node_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'创建节点失败: {str(e)}'
        }), 500

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
        with SSHClient(node=node) as ssh:
            # 连接成功即可
            node.status = 'online'
            node.last_seen = datetime.utcnow()
            db.session.commit()
            
            # 发送节点上线通知
            notification_service.notify_node_online(
                user_id=node.user_id,
                node_name=node.name,
                node_ip=node.ipaddress
            )
            
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
        
        # 发送节点离线通知
        notification_service.notify_node_offline(
            user_id=node.user_id,
            node_name=node.name,
            reason=f'连接测试失败: {str(e)}'
        )
        
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
@record_agent_event('update', lambda node_id: node_id)
def update_node(node_id):
    """更新节点"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        name = data.get('name')
        ipaddress = data.get('ipaddress')
        username = data.get('username')
        port = data.get('port')
        auth_type = data.get('auth_type')
        password = data.get('password')
        auth_key = data.get('key')
        config = data.get('config', {})
        group = data.get('group')
        tags = data.get('tags')
        description = data.get('description')

        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()
        if not node:
            AuditService.log_node_operation(
                user_id=current_user_id,
                action='update',
                node_id=node_id,
                node_name=name,
                details={'error': '节点不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '节点不存在'
            }), 404

        if name:
            node.name = name
        if ipaddress:
            node.ipaddress = ipaddress
        if username:
            node.username = username
        if password:
            node.password = password
        if port:
            node.port = port
        if auth_type:
            node.auth_type = auth_type
        if auth_key:
            node.auth_key = auth_key
        if config:
            node.config = config
        if description:
            node.description = description
        if group is not None:
            node.group = group
        if tags is not None:
            node.tags = tags

        db.session.commit()
        
        AuditService.log_node_operation(
            user_id=current_user_id,
            action='update',
            node_id=node.id,
            node_name=node.name,
            details={'msg': '节点更新成功'},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '节点更新成功',
            'data': node.to_dict()
        })
    except Exception as e:
        AuditService.log_node_operation(
            user_id=current_user_id,
            action='update',
            node_id=node_id,
            node_name=name,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': f'更新节点失败: {str(e)}'
        }), 500

@nodes_bp.route('/<string:node_id>', methods=['DELETE'])
@jwt_required()
@record_agent_event('delete', lambda node_id: node_id)
def delete_node(node_id):
    """删除节点"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()

        if not node:
            AuditService.log_node_operation(
                user_id=current_user_id,
                action='delete',
                node_id=node_id,
                node_name=None,
                details={'error': '节点不存在'},
                result='failed'
            )
            return jsonify({
                'status': 'error',
                'message': '节点不存在'
            }), 404

        # 删除相关监控数据
        MonitorData.query.filter_by(node_id=node.id).delete()

        node_name = node.name
        node_ip = node.ipaddress
        
        db.session.delete(node)
        db.session.commit()
        
        # 发送节点删除通知
        notification_service.create_notification(
            user_id=current_user_id,
            type='node_deleted',
            title=f'节点已删除: {node_name}',
            content=f'节点 {node_name} ({node_ip}) 已被删除。',
            level='info'
        )
        
        AuditService.log_node_operation(
            user_id=current_user_id,
            action='delete',
            node_id=node.id,
            node_name=node.name,
            details={'msg': '节点删除成功', 'ip_address': node.ipaddress},
            result='success'
        )
        return jsonify({
            'status': 'success',
            'message': '节点删除成功'
        })
    except Exception as e:
        db.session.rollback()
        AuditService.log_node_operation(
            user_id=current_user_id,
            action='delete',
            node_id=node_id,
            node_name=None,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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

@nodes_bp.route('/<string:node_id>/mount-check', methods=['POST'])
@jwt_required()
def node_mount_check(node_id):
    """
    挂载检测转发：主控收到请求后，转发给对应 Node（Proxy），返回检测结果
    """
    current_user_id = get_jwt_identity()
    node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()
    if not node:
        return jsonify({'status': 'error', 'message': '节点不存在'}), 404

    data = request.get_json()
    storage_config = data.get('storage_config')
    if not storage_config:
        return jsonify({'status': 'error', 'message': '缺少存储配置'}), 400

    try:
        # 通过 SSH 或 RPC 调用 Node 本地的挂载检测接口
        # 这里以 SSH 为例，实际可根据你的 Node agent 实现调整
        import json as pyjson
        with SSHClient(node) as ssh:
            cmd = f"easysync-agent mount-check '{pyjson.dumps(storage_config)}'"
            stdout, stderr, exit_code = ssh.execute_command(cmd)
            if exit_code != 0:
                return jsonify({'status': 'error', 'message': stderr}), 500
            result = pyjson.loads(stdout)
            return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'节点挂载检测失败: {str(e)}'}), 500

@nodes_bp.route('/groups', methods=['GET'])
@jwt_required()
def get_node_groups():
    """获取所有节点分组列表"""
    current_user_id = get_jwt_identity()
    groups = db.session.query(Node.group).filter_by(user_id=current_user_id).distinct().all()
    group_list = [g[0] for g in groups if g[0]]
    return jsonify({'status': 'success', 'data': group_list})

@nodes_bp.route('/tags', methods=['GET'])
@jwt_required()
def get_node_tags():
    """获取所有节点标签列表"""
    current_user_id = get_jwt_identity()
    tags = db.session.query(Node.tags).filter_by(user_id=current_user_id).all()
    tag_set = set()
    for t in tags:
        if t[0]:
            tag_set.update([tag.strip() for tag in t[0].split(',') if tag.strip()])
    return jsonify({'status': 'success', 'data': list(tag_set)})

@nodes_bp.route('/batch_group', methods=['POST'])
@jwt_required()
def batch_group_nodes():
    """批量分组节点"""
    data = request.get_json()
    node_ids = data.get('node_ids', [])
    group = data.get('group', '')
    current_user_id = get_jwt_identity()
    Node.query.filter(Node.id.in_(node_ids), Node.user_id == current_user_id).update({'group': group}, synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '批量分组成功'})

@nodes_bp.route('/batch_tags', methods=['POST'])
@jwt_required()
def batch_tag_nodes():
    """批量打标签节点"""
    data = request.get_json()
    node_ids = data.get('node_ids', [])
    tags = data.get('tags', '')
    current_user_id = get_jwt_identity()
    Node.query.filter(Node.id.in_(node_ids), Node.user_id == current_user_id).update({'tags': tags}, synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '批量打标签成功'})

@nodes_bp.route('/<string:node_id>/install', methods=['POST'])
@jwt_required()
def install_node_agent(node_id):
    """安装Proxy Agent"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first_or_404()
        
        # 获取请求参数
        data = request.get_json()
        install_path = data.get('install_path', '/opt/easysync/proxy')
        backup_path = '/opt/easysync/backups'
        log_path = '/opt/easysync/logs'
        
        # 更新节点状态
        node.agent_status = 'installing'
        db.session.commit()
        
        with SSHClient(node=node) as ssh:
            # 创建远程目录
            ssh.create_directory(install_path)
            ssh.create_directory(backup_path)
            ssh.create_directory(log_path)
            
            # 上传Proxy Agent文件
            proxy_dir = os.path.join(current_app.root_path, 'app/nodes/agent')
            logger.debug(f'上传文件: {proxy_dir}')

            # 上传主文件
            ssh.upload_file(
                os.path.join(proxy_dir, 'easysync-proxy.tar.gz'),
                f'{install_path}/easysync-proxy.tar.gz'
            )
            logger.debug(f'上传文件: {install_path}/easysync-proxy.tar.gz')

            # 解压文件
            stdout, stderr, exit_code = ssh.execute_command(
                f'tar -xzvf {install_path}/easysync-proxy.tar.gz -C {install_path}'
            )
            if exit_code != 0:
                raise Exception(f'解压失败: {stderr}')
            logger.debug(f'解压文件: {install_path}/easysync-proxy.tar.gz')

            # 获取服务器IP地址
            server_ip = request.host.split(':')[0]
            
            # 增加脚本可执行权限
            cmd = f'chmod +x {install_path}/install.sh'
            ssh.execute_command(cmd)
            
            # 执行安装脚本，传递三个参数
            install_cmd = f'{install_path}/install.sh {server_ip} {node_id} {current_user_id}'
            stdout, stderr, exit_code = ssh.execute_command(install_cmd)
            if exit_code != 0:
                raise Exception(f'安装失败: {stderr}')
            logger.debug(f'安装脚本执行结果: {stdout}')
            
            # 检查服务运行状态
            stdout, stderr, exit_code = ssh.execute_command('systemctl is-active easysync-proxy')
            if stdout.strip() != 'active':
                raise Exception('安装成功，但服务未启动')
            logger.debug(f'服务运行状态: {stdout}')

            # 更新节点状态
            node.agent_status = 'running'
            node.agent_version = '1.0.0'
            db.session.commit()
            
            # 发送Agent安装成功通知
            notification_service.create_notification(
                user_id=current_user_id,
                type='node_agent_installed',
                title=f'Agent安装成功: {node.name}',
                content=f'节点 {node.name} 的Proxy Agent已成功安装并启动。',
                level='success'
            )
            
            return jsonify({
                'status': 'success',
                'message': 'EasySync Proxy Agent安装成功'
            })
            
    except Exception as e:
        logger.error(f"安装Proxy Agent失败: {str(e)}")
        node.agent_status = 'install_error'
        db.session.commit()
        
        # 发送Agent安装失败通知
        notification_service.notify_node_error(
            user_id=current_user_id,
            node_name=node.name,
            error_message=f'Agent安装失败: {str(e)}'
        )
        
        return jsonify({
            'status': 'error',
            'message': f'安装失败: {str(e)}'
        }), 500

@nodes_bp.route('/<string:node_id>/uninstall', methods=['POST'])
@jwt_required()
def uninstall_node_agent(node_id):
    """卸载Proxy Agent"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first_or_404()
        
        # 更新节点状态
        node.agent_status = 'uninstalling'
        db.session.commit()
        
        with SSHClient(node=node) as ssh:
            # 停止服务
            ssh.execute_command('systemctl stop easysync-proxy')
            ssh.execute_command('systemctl disable easysync-proxy')
            
            # 删除服务文件
            ssh.execute_command('rm -f /etc/systemd/system/easysync-proxy.service')
            ssh.execute_command('systemctl daemon-reload')
            
            # 删除安装目录
            install_path = '/opt/easysync/proxy'
            backup_path = '/opt/easysync/backups'
            log_path = '/opt/easysync/logs'
            
            ssh.execute_command(f'rm -rf {install_path}')
            ssh.execute_command(f'rm -rf {backup_path}')
            ssh.execute_command(f'rm -rf {log_path}')
            
            # 更新节点状态
            node.agent_status = 'not_installed'
            node.agent_version = None
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Proxy Agent卸载成功'
            })
            
    except Exception as e:
        logger.error(f"卸载Proxy Agent失败: {str(e)}")
        node.agent_status = 'uninstall_error'
        db.session.commit()
        return jsonify({
            'status': 'error',
            'message': f'卸载失败: {str(e)}'
        }), 500

@nodes_bp.route('/<string:node_id>/status', methods=['POST'])
@jwt_required()
def get_node_status(node_id):
    """获取节点状态"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first_or_404()
        
        with SSHClient(node=node) as ssh:
            # 检查服务状态
            stdout, stderr, exit_code = ssh.execute_command('systemctl is-active easysync-proxy')
            service_status = stdout.strip()
            
            # 检查进程状态
            stdout, stderr, exit_code = ssh.execute_command('ps aux | grep "python3.*proxy.py" | grep -v grep')
            process_status = stdout.strip()
            
            # 检查日志文件
            log_path = '/opt/easysync/proxy/logs/proxy.log'
            stdout, stderr, exit_code = ssh.execute_command(f'tail -n 100 {log_path}')
            log_content = stdout
            
            # 检查配置文件
            config_path = '/opt/easysync/proxy/config/config.json'
            stdout, stderr, exit_code = ssh.execute_command(f'cat {config_path}')
            config_content = stdout
            
            # 获取版本信息
            stdout, stderr, exit_code = ssh.execute_command('hostname')
            hostname = stdout.strip()

            stdout, stderr, exit_code = ssh.execute_command('uname -s')
            os_type = stdout.strip()
        
            stdout, stderr, exit_code = ssh.execute_command('uname -r')
            os_version = stdout.strip()

            # 更新节点状态
            if service_status == 'active' and process_status:
                node.agent_status = 'running'
                node.status = 'online'
            else:
                node.agent_status = 'stopped'
                node.status = 'offline'
            
            node.last_heartbeat = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'service_status': service_status,
                    'process_status': bool(process_status),
                    'log_content': log_content,
                    'config_content': config_content,
                    'agent_status': node.agent_status,
                    'agent_version': node.agent_version,
                    'hostname': hostname,
                    'os_type': os_type,
                    'os_version': os_version,
                    'last_check': node.last_heartbeat.isoformat() if node.last_heartbeat else None
                }
            })
            
    except Exception as e:
        logger.error(f"获取节点状态失败: {str(e)}")
        node.agent_status = 'error'
        node.status = 'offline'
        node.last_heartbeat = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'status': 'error',
            'message': f'获取状态失败: {str(e)}'
        }), 500

@nodes_bp.route('/<string:node_id>/logs', methods=['GET'])
@jwt_required()
def get_node_logs(node_id):
    """获取节点日志"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first_or_404()
        
        # 获取请求参数
        lines = request.args.get('lines', 100, type=int)
        level = request.args.get('level', 'INFO')
        
        with SSHClient(node=node) as ssh:
            # 获取日志内容
            if level == 'DEBUG':
                log_path = '/opt/easysync/proxy/logs/agent.debug.log'
            else:
                log_path = '/opt/easysync/proxy/logs/agent.log'

            if level == 'ALL':
                command = f'tail -n {lines} {log_path}'
            else:
                command = f'grep -i "{level}" {log_path} | tail -n {lines}'
                
            stdout, stderr, exit_code = ssh.execute_command(command)
            log_content = stdout
            
            return jsonify({
                'status': 'success',
                'data': {
                    'log_content': log_content,
                    'level': level,
                    'lines': lines
                }
            })
            
    except Exception as e:
        logger.error(f"获取节点日志失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取日志失败: {str(e)}'
        }), 500

@nodes_bp.route('/<string:node_id>/processes', methods=['GET'])
@jwt_required()
def get_node_processes(node_id):
    """获取节点进程列表"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first_or_404()
        
        with SSHClient(node=node) as ssh:
            # 获取进程列表
            stdout, stderr, exit_code = ssh.execute_command('ps aux --sort=-%cpu | head -n 20')
            process_list = utils.parse_process_list(stdout)
            
            return jsonify({
                'status': 'success',
                'message': '获取进程列表成功',
                'data': process_list
            })
            
    except Exception as e:
        logger.error(f"获取进程列表失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取进程列表失败'
        }), 500

@nodes_bp.route('/batch_delete', methods=['POST'])
@jwt_required()
def batch_delete_nodes():
    """批量删除节点"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    node_ids = data.get('node_ids', [])
    if not node_ids:
        return jsonify({'status': 'error', 'message': '缺少node_ids'}), 400
    
    try:
        nodes = Node.query.filter(Node.id.in_(node_ids), Node.user_id == current_user_id).all()
        for node in nodes:
            db.session.delete(node)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'批量删除{len(nodes)}个节点成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@nodes_bp.route('/<string:node_id>/status-check', methods=['POST'])
@jwt_required()
def force_check_node_status(node_id):
    """强制检查节点状态"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()
        if not node:
            return jsonify({
                'status': 'error',
                'message': '节点不存在'
            }), 404
        
        # 使用状态监控器强制检查节点状态
        status_monitor = get_status_monitor()
        result = status_monitor.force_check_node(node_id)
        
        if 'error' in result:
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '节点状态检查完成',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"强制检查节点状态失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'检查失败: {str(e)}'
        }), 500

@nodes_bp.route('/<string:node_id>/health', methods=['GET'])
@jwt_required()
def get_node_health(node_id):
    """获取节点健康信息"""
    current_user_id = get_jwt_identity()
    try:
        node = Node.query.filter_by(id=node_id, user_id=current_user_id).first()
        if not node:
            return jsonify({
                'status': 'error',
                'message': '节点不存在'
            }), 404
        
        # 获取节点健康信息
        status_monitor = get_status_monitor()
        health_info = status_monitor.get_node_health_info(node_id)
        
        if 'error' in health_info:
            return jsonify({
                'status': 'error',
                'message': health_info['error']
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '获取节点健康信息成功',
            'data': health_info
        })
        
    except Exception as e:
        logger.error(f"获取节点健康信息失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取失败: {str(e)}'
        }), 500

@nodes_bp.route('/status-summary', methods=['GET'])
@jwt_required()
def get_nodes_status_summary():
    """获取所有节点状态摘要"""
    current_user_id = get_jwt_identity()
    try:
        nodes = Node.query.filter_by(user_id=current_user_id).all()
        
        summary = {
            'total_nodes': len(nodes),
            'online_nodes': 0,
            'offline_nodes': 0,
            'healthy_nodes': 0,
            'unhealthy_nodes': 0,
            'agent_status_summary': {
                'running': 0,
                'active': 0,
                'inactive': 0,
                'error': 0,
                'not_installed': 0
            },
            'nodes_detail': []
        }
        
        status_monitor = get_status_monitor()
        
        for node in nodes:
            # 获取健康信息
            health_info = status_monitor.get_node_health_info(node.id)
            
            # 统计在线/离线状态
            if node.status == 'online':
                summary['online_nodes'] += 1
            else:
                summary['offline_nodes'] += 1
            
            # 统计健康状态
            if health_info.get('is_healthy', False):
                summary['healthy_nodes'] += 1
            else:
                summary['unhealthy_nodes'] += 1
            
            # 统计Agent状态
            agent_status = node.agent_status or 'not_installed'
            if agent_status in summary['agent_status_summary']:
                summary['agent_status_summary'][agent_status] += 1
            
            # 添加节点详情
            summary['nodes_detail'].append({
                'id': node.id,
                'name': node.name,
                'ipaddress': node.ipaddress,
                'status': node.status,
                'agent_status': node.agent_status,
                'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                'is_healthy': health_info.get('is_healthy', False),
                'heartbeat_status': health_info.get('heartbeat_status', 'unknown')
            })
        
        return jsonify({
            'status': 'success',
            'message': '获取节点状态摘要成功',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"获取节点状态摘要失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取失败: {str(e)}'
        }), 500