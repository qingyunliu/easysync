from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import psutil
from datetime import datetime, timedelta
from backend.app.models import Storage, Task, Notification, Client, Node
from . import dashboard_bp

@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """获取仪表盘数据"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取存储节点统计
        storages = Storage.query.filter_by(user_id=current_user_id).all()
        storage_count = len(storages)

        # 获取客户端统计
        clients = Client.query.filter_by(user_id=current_user_id).all()
        client_count = len(clients)
        online_clients = sum(1 for c in clients if c.status == 'online')
        offline_clients = client_count - online_clients
        installed_agents = sum(1 for c in clients if c.agent_status == 'installed')
        uninstalled_agents = client_count - installed_agents

        # 获取node统计
        nodes = Node.query.filter_by(user_id=current_user_id).all()
        node_count = len(nodes)
        online_nodes = sum(1 for n in nodes if n.status == 'online')
        offline_nodes = node_count - online_nodes
        installed_nodes = sum(1 for n in nodes if n.agent_status == 'installed')
        uninstalled_nodes = node_count - installed_nodes
        
        # 获取任务统计
        tasks = Task.query.filter_by(user_id=current_user_id).all()
        task_count = len(tasks)
        running_count = sum(1 for t in tasks if t.status == 'running')
        stopped_count = task_count - running_count
        
        # 获取今日同步统计
        today = datetime.now().date()
        today_jobs = Task.query.filter(
            Task.created_at >= today,
            Task.created_at < today + timedelta(days=1),
            Task.user_id == current_user_id
        ).all()
        
        today_sync_count = len(today_jobs)
        today_success_count = sum(1 for job in today_jobs if job.status == 'completed')
        today_failed_count = sum(1 for job in today_jobs if job.status == 'failed')
        
        # 获取系统状态
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # 获取网络流量
        net_io = psutil.net_io_counters()
        network_traffic = net_io.bytes_sent + net_io.bytes_recv
        
        system_status = '正常'
        if cpu_usage > 90 or memory_usage > 90 or disk_usage > 90:
            system_status = '警告'
        elif cpu_usage > 70 or memory_usage > 70 or disk_usage > 70:
            system_status = '注意'
        
        # 获取最近任务
        recent_tasks = Task.query.filter_by(user_id=current_user_id).order_by(
            Task.created_at.desc()
        ).limit(5).all()
        recent_tasks_data = [{
            'name': task.name if task.name else '未知任务',
            'status': task.status,
            'start_time': task.started_at.isoformat() if task.started_at else None,
            'end_time': task.completed_at.isoformat() if task.completed_at else None
        } for task in recent_tasks]
        
        # 获取最近通知
        recent_notifications = Notification.query.filter_by(
            user_id=current_user_id
        ).order_by(
            Notification.created_at.desc()
        ).limit(5).all()
        recent_notifications_data = [notification.to_dict() for notification in recent_notifications]
        
        return jsonify({
            'status': 'success',
            'message': '仪表盘数据获取成功',
            'data': {
                'storages': {
                    'storageCount': storage_count,
                    'mountedCount': 0,
                    'unmountedCount': 0,
                    'totalStorageSize': 0,
                    'usedStorageSize': 0,
                },
                'clients': {
                    'clientCount': client_count,
                    'onlineClients': online_clients,
                    'offlineClients': offline_clients,
                    'installedAgents': installed_agents,
                    'uninstalledAgents': uninstalled_agents,
                },
                'nodes': {
                    'nodeCount': node_count,
                    'onlineNodes': online_nodes,
                    'offlineNodes': offline_nodes,
                    'installedNodes': installed_nodes,
                    'uninstalledNodes': uninstalled_nodes,
                },
                'tasks': {
                    'taskCount': task_count,
                    'runningCount': running_count,
                    'stoppedCount': stopped_count,
                    'todaySyncCount': today_sync_count,
                    'todaySuccessCount': today_success_count,
                    'todayFailedCount': today_failed_count,
                },
                'system': {
                    'systemStatus': system_status,
                    'cpuUsage': cpu_usage,
                    'memoryUsage': memory_usage,
                    'diskUsage': disk_usage,
                    'networkTraffic': network_traffic
                },
                'recent_tasks': recent_tasks_data,
                'recent_notifications': recent_notifications_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500 