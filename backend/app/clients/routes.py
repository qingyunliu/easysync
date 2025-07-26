from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.models import Client, AuditLog, MonitorData
from backend import db
from datetime import datetime
from . import clients_bp
import os
import logging
import tempfile
import yaml
import uuid
from ..utils.ssh_utils import SSHClient
from ..utils import utils

logger = logging.getLogger(__name__)

@clients_bp.route('', methods=['GET'])
@jwt_required()
def get_clients():
    """获取当前用户的所有服务器列表"""
    current_user_id = get_jwt_identity()
    clients = Client.query.filter_by(user_id=current_user_id).all()
    return jsonify({
        'status': 'success',
        'message': '服务器列表获取成功',
        'data': [client.to_dict() for client in clients]
    }), 200

@clients_bp.route('', methods=['POST'])
@jwt_required()
def create_client():
    """创建新的服务器"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 验证必填字段
    if data.get('auth_type') == 'password':
        required_fields = ['name', 'ip_address', 'username', 'password', 'port']
    else:
        required_fields = ['name', 'ip_address', 'username', 'ssh_key', 'port']

    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    # 创建新服务器
    client = Client(
        name=data['name'],
        ip_address=data['ip_address'],
        username=data['username'],
        auth_type=data['auth_type'],
        port=data.get('port', 22),
        password=data.get('password'),
        ssh_key=data.get('ssh_key'),
        description=data.get('description'),
        user_id=current_user_id
    )
    
    try:
        db.session.add(client)
        db.session.commit()
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user_id,
            action='create',
            resource_type='client',
            resource_id=client.id,
            details={'name': client.name, 'ip_address': client.ip_address}
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '服务器创建成功',
            'data': client.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clients_bp.route('/<string:client_id>', methods=['PUT'])
@jwt_required()
def update_client(client_id):
    """更新服务器信息"""
    current_user_id = get_jwt_identity()
    client = Client.query.filter_by(id=client_id, user_id=current_user_id).first_or_404()
    
    data = request.get_json()
    for key, value in data.items():
        if hasattr(client, key):
            setattr(client, key, value)
    
    try:
        db.session.commit()
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user_id,
            action='update',
            resource_type='client',
            resource_id=client.id,
            details={'name': client.name, 'ip_address': client.ip_address}
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '服务器更新成功',
            'data': client.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clients_bp.route('/<string:client_id>', methods=['DELETE'])
@jwt_required()
def delete_client(client_id):
    """删除服务器"""
    current_user_id = get_jwt_identity()
    client = Client.query.filter_by(id=client_id, user_id=current_user_id).first_or_404()
    
    try:
        # 删除相关监控数据
        MonitorData.query.filter_by(client_id=client.id).delete()

        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user_id,
            action='delete',
            resource_type='client',
            resource_id=client.id,
            details={'name': client.name, 'ip_address': client.ip_address}
        )
        db.session.add(audit_log)
        
        db.session.delete(client)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': '服务器删除成功'
        }), 204
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clients_bp.route('/<string:client_id>/install', methods=['POST'])
@jwt_required()
def install_agent(client_id):
    """安装Agent"""
    current_user_id = get_jwt_identity()
    try:
        client = Client.query.filter_by(id=client_id, user_id=current_user_id).first_or_404()
        
        # 获取请求参数
        data = request.get_json()
        install_path = data.get('install_path', current_app.config['EASYSYNC_AGENT_INSTALL_PATH'])
        backup_path = current_app.config['EASYSYNC_AGENT_BACKUP_PATH']
        log_path = current_app.config['EASYSYNC_AGENT_LOG_PATH']
        
        # 更新客户端状态
        client.agent_status = 'installing'
        db.session.commit()
        
        with SSHClient(client=client) as ssh:
            # 创建远程目录
            ssh.create_directory(install_path)
            ssh.create_directory(backup_path)
            ssh.create_directory(log_path)
            
            # 上传Agent文件
            agent_dir = os.path.join(current_app.root_path, 'app/clients/agent/python')
            logger.debug(f'上传文件: {agent_dir}')

            # 上传主文件
            ssh.upload_file(
                os.path.join(agent_dir, 'easysync-agent.tar.gz'),
                f'{install_path}/easysync-agent.tar.gz'
            )
            logger.debug(f'上传文件: {install_path}/easysync-agent.tar.gz')

            # 解压文件
            stdout, stderr, exit_code = ssh.execute_command(
                f'tar -xzvf {install_path}/easysync-agent.tar.gz -C {install_path}'
            )
            if exit_code != 0:
                raise Exception(f'解压失败: {stderr}')
            logger.debug(f'解压文件: {install_path}/easysync-agent.tar.gz')

            # 重命名目录
            stdout, stderr, exit_code = ssh.execute_command(
                f'mv {install_path}/easysync-agent {install_path}/agent'
            )
            if exit_code != 0:
                raise Exception(f'重命名失败: {stderr}')
            logger.debug(f'重命名目录完成')

            # 获取服务器IP地址
            server_ip = request.host.split(':')[0]  # 获取当前服务器IP
            
            # 执行安装脚本，传递三个参数
            install_cmd = f'{install_path}/agent/install.sh {server_ip} {client_id} {current_user_id}'
            stdout, stderr, exit_code = ssh.execute_command(install_cmd)
            if exit_code != 0:
                raise Exception(f'安装失败: {stderr}')
            logger.debug(f'安装脚本执行结果: {stdout}')
            
            # 检查服务运行状态
            stdout, stderr, exit_code = ssh.execute_command('systemctl is-active easysync-agent')
            if stdout.strip() != 'active':
                raise Exception('安装成功，但服务未启动')
            logger.debug(f'服务运行状态: {stdout}')

            # 更新客户端状态
            client.agent_status = 'running'
            client.agent_version = '1.0.0'
            client.agent_install_path = install_path
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Agent安装成功'
            })
            
    except Exception as e:
        logger.error(f"安装Agent失败: {str(e)}")
        client.agent_status = 'install_error'
        db.session.commit()
        return jsonify({
            'status': 'error',
            'message': f'安装失败: {str(e)}'
        }), 500

@clients_bp.route('/<string:client_id>/uninstall', methods=['POST'])
@jwt_required()
def uninstall_agent(client_id):
    """卸载Agent"""
    try:
        client = Client.query.get_or_404(client_id)
        
        # 更新客户端状态
        client.agent_status = 'uninstalling'
        db.session.commit()
        
        with SSHClient(client=client) as ssh:
            # 停止服务
            ssh.execute_command('systemctl stop easysync-agent')
            ssh.execute_command('systemctl disable easysync-agent')
            
            # 删除服务文件
            ssh.execute_command('rm -f /etc/systemd/system/easysync-agent.service')
            ssh.execute_command('systemctl daemon-reload')
            
            # 删除安装目录
            install_path = current_app.config['EASYSYNC_AGENT_INSTALL_PATH']
            backup_path = current_app.config['EASYSYNC_AGENT_BACKUP_PATH']
            log_path = current_app.config['EASYSYNC_AGENT_LOG_PATH']
            
            ssh.execute_command(f'rm -rf {install_path}')
            ssh.execute_command(f'rm -rf {backup_path}')
            ssh.execute_command(f'rm -rf {log_path}')
            
            # 更新客户端状态
            client.agent_status = 'not_installed'
            client.agent_version = None
            client.agent_install_path = None
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Agent卸载成功'
            }), 200
            
    except Exception as e:
        logger.error(f"卸载Agent失败: {str(e)}")
        client.agent_status = 'uninstall_error'
        db.session.commit()
        return jsonify({
            'status': 'error',
            'message': f'卸载失败: {str(e)}'
        }), 500

@clients_bp.route('/<string:client_id>/status', methods=['POST'])
@jwt_required()
def get_client_status(client_id):
    """获取客户端状态"""
    try:
        client = Client.query.get_or_404(client_id)
        
        with SSHClient(client=client) as ssh:
            # 检查服务状态
            stdout, stderr, exit_code = ssh.execute_command('systemctl is-active easysync-agent')
            service_status = stdout.strip()
            
            # 检查进程状态
            stdout, stderr, exit_code = ssh.execute_command('ps aux | grep "python3.*client.py" | grep -v grep')
            process_status = stdout.strip()
            
            # 检查日志文件
            log_path = current_app.config['EASYSYNC_AGENT_LOG_PATH']
            stdout, stderr, exit_code = ssh.execute_command(f'tail -n 100 {log_path}')
            log_content = stdout
            
            # 检查配置文件
            install_path = current_app.config['EASYSYNC_AGENT_INSTALL_PATH']
            stdout, stderr, exit_code = ssh.execute_command(f'cat {install_path}/agent/config.yaml')
            config_content = stdout
            
            # 检查Python依赖
            stdout, stderr, exit_code = ssh.execute_command('pip list | grep -E "Flask|Flask-SocketIO|python-socketio|python-engineio|PyYAML|psutil"')
            dependencies = stdout

            # 获取版本信息
            stdout, stderr, exit_code = ssh.execute_command('hostname')
            hostname = stdout.strip()

            stdout, stderr, exit_code = ssh.execute_command('uname -s')
            os_type = stdout.strip()
        
            stdout, stderr, exit_code = ssh.execute_command('uname -r')
            os_version = stdout.strip()

            stdout, stderr, exit_code = ssh.execute_command('cat /proc/cpuinfo | grep "model name" | head -n 1')
            cpu_info = stdout.strip()
        
            stdout, stderr, exit_code = ssh.execute_command('free -h | grep Mem')
            memory_info = stdout.strip()
        
            stdout, stderr, exit_code = ssh.execute_command('df -h')
            disk_info = stdout.strip()

            # 更新服务器信息
            client.hostname = hostname
            client.os_type = os_type
            client.os_version = os_version
            client.cpu_info = cpu_info
            client.memory_info = memory_info
            client.disk_info = disk_info
            
            # 更新客户端状态
            if service_status == 'active' and process_status:
                client.agent_status = 'running'
            else:
                client.agent_status = 'stopped'
            
            client.last_check = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'service_status': service_status,
                    'process_status': bool(process_status),
                    'log_content': log_content,
                    'config_content': config_content,
                    'dependencies': dependencies,
                    'agent_status': client.agent_status,
                    'agent_version': client.agent_version,
                    'last_check': client.last_check.isoformat()
                }
            }), 200
            
    except Exception as e:
        logger.error(f"获取客户端状态失败: {str(e)}")
        client.agent_status = 'error'
        client.last_check = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'status': 'error',
            'message': f'获取状态失败: {str(e)}'
        }), 500

@clients_bp.route('/<string:client_id>/test-connection', methods=['POST'])
@jwt_required()
def test_connection(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        if str(client.user_id) != get_jwt_identity():
            return jsonify({'error': '无权访问此服务器'}), 403

        # 测试SSH连接
        with SSHClient(client=client) as ssh:
            # 连接成功即可
            client.status = 'online'
            client.last_seen = datetime.utcnow()
            db.session.commit()
            
            # 记录审计日志
            audit_log = AuditLog(
                user_id=client.user_id,
                action='test_connection',
                resource_type='client',
                resource_id=client.id,
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
        client.status = 'offline'
        db.session.commit()
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=client.user_id,
            action='test_connection',
            resource_type='client',
            resource_id=client.id,
            details={'status': 'failed', 'error': str(e)}
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }), 400

@clients_bp.route('/<string:client_id>/detail', methods=['GET'])
def get_client_detail(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        
        with SSHClient(client=client) as ssh:
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

@clients_bp.route('/<string:client_id>/monitor', methods=['GET'])
@jwt_required()
def get_client_monitor(client_id):
    """获取客户端监控数据"""
    try:
        client = Client.query.get_or_404(client_id)
        
        with SSHClient(client=client) as ssh:
            # 获取CPU使用率
            stdout, stderr, exit_code = ssh.execute_command('top -bn1 | grep "Cpu(s)"')
            cpu_usage = utils.parse_cpu_usage(stdout)
            
            # 获取内存使用率
            stdout, stderr, exit_code = ssh.execute_command('free -m')
            memory_usage = utils.parse_memory_usage(stdout)
            
            # 获取磁盘使用率
            stdout, stderr, exit_code = ssh.execute_command('df -h')
            disk_usage = utils.parse_disk_usage(stdout)
            
            # 获取网络流量
            stdout, stderr, exit_code = ssh.execute_command('cat /proc/net/dev')
            network_traffic = utils.parse_network_traffic(stdout)
            
            # 获取进程列表
            stdout, stderr, exit_code = ssh.execute_command('ps aux --sort=-%cpu | head -n 10')
            process_list = utils.parse_process_list(stdout)
            
            # 获取系统负载
            stdout, stderr, exit_code = ssh.execute_command('cat /proc/loadavg')
            load_avg = stdout.strip().split()
            
            # 获取系统运行时间
            stdout, stderr, exit_code = ssh.execute_command('uptime -p')
            uptime = stdout.strip()
            
            # 保存监控数据
            monitor_data = {
                'cpu': {
                    'usage': cpu_usage,
                    'load_avg': {
                        '1min': float(load_avg[0]),
                        '5min': float(load_avg[1]),
                        '15min': float(load_avg[2])
                    }
                },
                'memory': memory_usage,
                'disk': disk_usage,
                'network': network_traffic,
                'processes': process_list,
                'uptime': uptime
            }
            
            save_monitor_data(client_id, monitor_data)
            
            return jsonify({
                'status': 'success',
                'data': monitor_data
            }), 200
            
    except Exception as e:
        logger.error(f"获取客户端监控数据失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取监控数据失败: {str(e)}'
        }), 500

@clients_bp.route('/<string:client_id>/processes', methods=['GET'])
def get_client_processes(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        
        with SSHClient(client=client) as ssh:
            # 获取进程列表
            stdout, stderr, exit_code = ssh.execute_command('ps aux --sort=-%cpu | head -n 10')
            process_list = utils.parse_process_list(stdout)
            
            return jsonify({
                'status': 'success',
                'message': '获取进程列表成功',
                'data': process_list
            }), 200
            
    except Exception as e:
        logging.error(f"获取进程列表失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取进程列表失败'
        }), 500

@clients_bp.route('/<string:client_id>/sync', methods=['POST'])
def create_sync_task(client_id):
    """创建同步任务"""
    try:
        client = Client.query.get_or_404(client_id)
        
        # 获取任务参数
        data = request.get_json()
        task = {
            'id': str(uuid.uuid4()),
            'source': data.get('source'),
            'destination': data.get('destination'),
            'options': data.get('options', {}),
            'schedule': data.get('schedule', {})
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Sync task created successfully',
            'task_id': task['id']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clients_bp.route('/<string:client_id>/upgrade', methods=['POST'])
@jwt_required()
def upgrade_agent(client_id):
    """升级Agent"""
    try:
        client = Client.query.get_or_404(client_id)
        
        # 获取请求参数
        data = request.get_json()
        version = data.get('version')
        if not version:
            return jsonify({
                'status': 'error',
                'message': '缺少版本号参数'
            }), 400
            
        # 更新客户端状态
        client.agent_status = 'upgrading'
        db.session.commit()
        
        with SSHClient(client=client) as ssh:
            # 停止服务
            ssh.exec_command('systemctl stop easysync-agent')
            
            # 备份当前版本
            install_path = client.agent_install_path or '/opt/easysync/agent'
            backup_path = '/opt/easysync/backups'
            backup_dir = f"{backup_path}/agent-{client.agent_version}"
            
            ssh.exec_command(f'mkdir -p {backup_dir}')
            ssh.exec_command(f'cp -r {install_path}/* {backup_dir}/')
            
            # 上传新版本文件
            sftp = ssh.open_sftp()
            agent_dir = os.path.join(current_app.root_path, 'app/clients/agent')
            
            # 上传主文件
            sftp.put(os.path.join(agent_dir, 'client.py'), f'{install_path}/client.py')
            sftp.put(os.path.join(agent_dir, 'requirements.txt'), f'{install_path}/requirements.txt')
            
            # 上传模块
            modules_dir = os.path.join(install_path, 'modules')
            ssh.exec_command(f'mkdir -p {modules_dir}')
            
            for module_file in os.listdir(os.path.join(agent_dir, 'modules')):
                if module_file.endswith('.py'):
                    sftp.put(
                        os.path.join(agent_dir, 'modules', module_file),
                        f'{modules_dir}/{module_file}'
                    )
            
            # 更新配置文件
            config = {
                'client': {
                    'id': client.client_id,
                    'version': version,
                    'name': client.name,
                    'description': client.description
                },
                'server': {
                    'url': f"http://{request.host}",
                    'ws_path': '/ws/socket.io',
                    'heartbeat_interval': 30
                },
                'monitor': {
                    'interval': 5,
                    'metrics': ['cpu', 'memory', 'disk', 'network']
                },
                'log': {
                    'level': 'INFO',
                    'file': '/var/log/easysync/agent.log',
                    'max_size': 10485760,
                    'backup_count': 5
                },
                'upgrade': {
                    'url': f"http://{request.host}/upgrade",
                    'backup_dir': backup_path,
                    'check_interval': 3600
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config, f)
                config_path = f.name
            
            sftp.put(config_path, f'{install_path}/config.yaml')
            
            # 安装Python依赖
            ssh.exec_command(f'pip install -r {install_path}/requirements.txt')
            
            # 启动服务
            ssh.exec_command('systemctl start easysync-agent')
            
            # 更新客户端状态
            client.agent_status = 'running'
            client.agent_version = version
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Agent升级成功'
            }), 200
            
    except Exception as e:
        logger.error(f"升级Agent失败: {str(e)}")
        client.agent_status = 'error'
        db.session.commit()
        return jsonify({
            'status': 'error',
            'message': f'升级失败: {str(e)}'
        }), 500

@clients_bp.route('/<string:client_id>/logs', methods=['GET'])
@jwt_required()
def get_client_logs(client_id):
    """获取客户端日志"""
    try:
        client = Client.query.get_or_404(client_id)
        
        # 获取请求参数
        lines = request.args.get('lines', 100, type=int)
        level = request.args.get('level', 'INFO')
        
        with SSHClient(client=client) as ssh:
            try:
                # 获取日志内容
                log_path = '/opt/easysync/agent/logs/agent.log'
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
                }), 200
                
            finally:
                ssh.close()
            
    except Exception as e:
        logger.error(f"获取客户端日志失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取日志失败: {str(e)}'
        }), 500

@clients_bp.route('/<string:client_id>/config', methods=['GET', 'PUT'])
@jwt_required()
def manage_client_config(client_id):
    """管理客户端配置"""
    try:
        client = Client.query.get_or_404(client_id)
        
        with SSHClient(client=client) as ssh:
            try:
                install_path = client.agent_install_path or '/opt/easysync/agent'
                config_path = f'{install_path}/config.yaml'
                
                if request.method == 'GET':
                    # 获取配置
                    stdin, stdout, stderr = ssh.execute_command(f'cat {config_path}')
                    config_content = stdout.read().decode()
                    
                    return jsonify({
                        'status': 'success',
                        'data': {
                            'config': yaml.safe_load(config_content)
                        }
                    }), 200
                    
                else:  # PUT
                    # 更新配置
                    new_config = request.get_json()
                    if not new_config:
                        return jsonify({
                            'status': 'error',
                            'message': '缺少配置数据'
                        }), 400
                    
                    # 备份当前配置
                    backup_path = f'{config_path}.{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    ssh.execute_command(f'cp {config_path} {backup_path}')
                    
                    # 写入新配置
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                        yaml.dump(new_config, f)
                        config_path = f.name
                    
                    sftp = ssh.open_sftp()
                    sftp.put(config_path, f'{install_path}/config.yaml')
                    
                    # 重启服务
                    ssh.execute_command('systemctl restart easysync-agent')
                    
                    return jsonify({
                        'status': 'success',
                        'message': '配置更新成功'
                    }), 200
                    
            finally:
                if 'config_path' in locals():
                    os.unlink(config_path)
                ssh.close()
            
    except Exception as e:
        logger.error(f"管理客户端配置失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'配置管理失败: {str(e)}'
        }), 500

def save_monitor_data(client_id, monitor_data):
    """保存监控数据"""
    try:
        data = MonitorData(
            client_id=client_id,
            cpu_usage=monitor_data['cpu']['usage'],
            cpu_load_1min=monitor_data['cpu']['load_avg']['1min'],
            cpu_load_5min=monitor_data['cpu']['load_avg']['5min'],
            cpu_load_15min=monitor_data['cpu']['load_avg']['15min'],
            memory_total=monitor_data['memory']['total'],
            memory_used=monitor_data['memory']['used'],
            memory_free=monitor_data['memory']['free'],
            memory_usage_percent=monitor_data['memory']['usage_percent'],
            disk_data=monitor_data['disk'],
            network_data=monitor_data['network'],
            process_data=monitor_data['processes'],
            uptime=monitor_data['uptime']
        )
        
        db.session.add(data)
        db.session.commit()
        
    except Exception as e:
        logger.error(f"保存监控数据失败: {str(e)}")
        db.session.rollback()
        raise e

@clients_bp.route('/heartbeat', methods=['POST'])
def client_heartbeat():
    """客户端心跳上报接口（Agent定时调用）"""
    data = request.get_json()
    client_id = data.get('client_id')
    user_id = data.get('user_id')
    resource_info = data.get('resource_info', {})
    now = datetime.utcnow()

    if not client_id or not user_id:
        return jsonify({'status': 'error', 'message': '缺少client_id或user_id'}), 400

    client = Client.query.filter_by(id=client_id, user_id=user_id).first()
    if not client:
        # 支持首次上线自动注册
        client = Client(
            id=client_id,
            user_id=user_id,
            name=data.get('name', f'Agent-{client_id[:8]}'),
            ip_address=data.get('ip_address', ''),
            agent_status='running',
            last_seen=now
        )
        db.session.add(client)
    else:
        client.agent_status = 'running'
        client.last_seen = now
        # 更新资源信息
        if 'cpu' in resource_info:
            client.cpu_info = resource_info['cpu']
        if 'memory' in resource_info:
            client.memory_info = resource_info['memory']
        if 'disk' in resource_info:
            client.disk_info = resource_info['disk']
        if 'os_type' in resource_info:
            client.os_type = resource_info['os_type']
        if 'os_version' in resource_info:
            client.os_version = resource_info['os_version']
        if 'hostname' in resource_info:
            client.hostname = resource_info['hostname']
    db.session.commit()
    return jsonify({'status': 'success', 'message': '心跳上报成功'})

@clients_bp.route('/batch_delete', methods=['POST'])
@jwt_required()
def batch_delete_clients():
    """批量删除服务器"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    client_ids = data.get('client_ids', [])
    if not client_ids:
        return jsonify({'status': 'error', 'message': '缺少client_ids'}), 400
    try:
        clients = Client.query.filter(Client.id.in_(client_ids), Client.user_id == current_user_id).all()
        for client in clients:
            db.session.delete(client)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'批量删除{len(clients)}台服务器成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@clients_bp.route('/batch_group', methods=['POST'])
@jwt_required()
def batch_group_clients():
    """批量分组"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    client_ids = data.get('client_ids', [])
    group = data.get('group', 'default')
    if not client_ids:
        return jsonify({'status': 'error', 'message': '缺少client_ids'}), 400
    try:
        clients = Client.query.filter(Client.id.in_(client_ids), Client.user_id == current_user_id).all()
        for client in clients:
            client.group = group
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'批量分组{len(clients)}台服务器到{group}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@clients_bp.route('/batch_tags', methods=['POST'])
@jwt_required()
def batch_tag_clients():
    """批量打标签（覆盖式）"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    client_ids = data.get('client_ids', [])
    tags = data.get('tags', '')
    if not client_ids:
        return jsonify({'status': 'error', 'message': '缺少client_ids'}), 400
    try:
        clients = Client.query.filter(Client.id.in_(client_ids), Client.user_id == current_user_id).all()
        for client in clients:
            client.tags = tags
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'批量打标签成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@clients_bp.route('/groups', methods=['GET'])
@jwt_required()
def get_all_groups():
    """获取所有分组列表"""
    current_user_id = get_jwt_identity()
    groups = db.session.query(Client.group).filter_by(user_id=current_user_id).distinct().all()
    group_list = [g[0] for g in groups if g[0]]
    return jsonify({'status': 'success', 'data': group_list, 'message': '分组列表获取成功'})

@clients_bp.route('/tags', methods=['GET'])
@jwt_required()
def get_all_tags():
    """获取所有标签列表（去重）"""
    current_user_id = get_jwt_identity()
    tags = db.session.query(Client.tags).filter_by(user_id=current_user_id).all()
    tag_set = set()
    for tag_str in tags:
        if tag_str[0]:
            tag_set.update([t.strip() for t in tag_str[0].split(',') if t.strip()])
    return jsonify({'status': 'success', 'data': list(tag_set), 'message': '标签列表获取成功'})