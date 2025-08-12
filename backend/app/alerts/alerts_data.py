"""
告警系统数据初始化脚本
用于填充默认的资源类型、事件类型等基础数据
"""

import logging
from backend import db
from backend.app.models.alert import (
    AlertResourceType, AlertResourceItem, 
    AlertEventType, AlertEventAction, AlertEventResult
)

logger = logging.getLogger(__name__)


def init_alert_resource_types():
    """初始化告警资源类型"""
    try:
        if AlertResourceType.query.count() > 0:
            logger.info("告警资源类型已存在，跳过初始化")
            return
        
        resource_types = [
            {'name': '系统资源', 'code': 'system', 'description': '系统级别的资源监控', 'category': 'system', 'icon': 'computer', 'sort_order': 1},
            {'name': '存储资源', 'code': 'storage', 'description': '存储相关的资源监控', 'category': 'storage', 'icon': 'storage', 'sort_order': 2},
            {'name': '网络资源', 'code': 'network', 'description': '网络相关的资源监控', 'category': 'network', 'icon': 'network_check', 'sort_order': 3},
            {'name': '客户端资源', 'code': 'client', 'description': '客户端相关的资源监控', 'category': 'client', 'icon': 'devices', 'sort_order': 4},
            {'name': '节点资源', 'code': 'node', 'description': '同步节点相关的资源监控', 'category': 'node', 'icon': 'hub', 'sort_order': 5}
        ]
        
        for rt_data in resource_types:
            resource_type = AlertResourceType(**rt_data)
            db.session.add(resource_type)
        
        db.session.commit()
        logger.info("告警资源类型初始化完成")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"初始化告警资源类型失败: {e}")
        raise


def init_alert_resource_items():
    """初始化告警资源条目"""
    try:
        if AlertResourceItem.query.count() > 0:
            logger.info("告警资源条目已存在，跳过初始化")
            return
        
        # 获取资源类型
        system_type = AlertResourceType.query.filter_by(code='system').first()
        storage_type = AlertResourceType.query.filter_by(code='storage').first()
        network_type = AlertResourceType.query.filter_by(code='network').first()
        client_type = AlertResourceType.query.filter_by(code='client').first()
        node_type = AlertResourceType.query.filter_by(code='node').first()
        
        resource_items = [
            # 系统资源条目
            {'resource_type_id': system_type.id, 'name': 'CPU使用率', 'code': 'cpu_percent', 'description': 'CPU使用率百分比', 'unit': '%', 'data_type': 'float', 'default_threshold': 80.0, 'min_value': 0.0, 'max_value': 100.0, 'operators': ['>', '>=', '<', '<='], 'sort_order': 1},
            {'resource_type_id': system_type.id, 'name': '内存使用率', 'code': 'memory_percent', 'description': '内存使用率百分比', 'unit': '%', 'data_type': 'float', 'default_threshold': 85.0, 'min_value': 0.0, 'max_value': 100.0, 'operators': ['>', '>=', '<', '<='], 'sort_order': 2},
            {'resource_type_id': system_type.id, 'name': '磁盘使用率', 'code': 'disk_percent', 'description': '磁盘使用率百分比', 'unit': '%', 'data_type': 'float', 'default_threshold': 90.0, 'min_value': 0.0, 'max_value': 100.0, 'operators': ['>', '>=', '<', '<='], 'sort_order': 3},
            {'resource_type_id': system_type.id, 'name': '系统负载', 'code': 'load_average', 'description': '系统平均负载', 'unit': '', 'data_type': 'float', 'default_threshold': 2.0, 'min_value': 0.0, 'max_value': 100.0, 'operators': ['>', '>=', '<', '<='], 'sort_order': 4},
            
            # 存储资源条目
            {'resource_type_id': storage_type.id, 'name': '存储状态', 'code': 'storage_status', 'description': '存储连接状态', 'unit': '', 'data_type': 'string', 'default_threshold': 0, 'min_value': 0, 'max_value': 1, 'operators': ['==', '!='], 'sort_order': 1},
            {'resource_type_id': storage_type.id, 'name': '存储连接时间', 'code': 'storage_connection_time', 'description': '存储连接响应时间', 'unit': 'ms', 'data_type': 'float', 'default_threshold': 5000.0, 'min_value': 0.0, 'max_value': 60000.0, 'operators': ['>', '>=', '<', '<='], 'sort_order': 2},
            {'resource_type_id': storage_type.id, 'name': '存储可用空间', 'code': 'storage_free_space', 'description': '存储可用空间百分比', 'unit': '%', 'data_type': 'float', 'default_threshold': 10.0, 'min_value': 0.0, 'max_value': 100.0, 'operators': ['<', '<=', '>', '>='], 'sort_order': 3},
            
            # 网络资源条目
            {'resource_type_id': network_type.id, 'name': '网络延迟', 'code': 'network_latency', 'description': '网络延迟时间', 'unit': 'ms', 'data_type': 'float', 'default_threshold': 100.0, 'min_value': 0.0, 'max_value': 10000.0, 'operators': ['>', '>=', '<', '<='], 'sort_order': 1},
            {'resource_type_id': network_type.id, 'name': '网络连接数', 'code': 'network_connections', 'description': '当前网络连接数', 'unit': '个', 'data_type': 'int', 'default_threshold': 1000, 'min_value': 0, 'max_value': 100000, 'operators': ['>', '>=', '<', '<='], 'sort_order': 2},
            
            # 客户端资源条目
            {'resource_type_id': client_type.id, 'name': '客户端连接状态', 'code': 'client_connection_status', 'description': '客户端连接状态', 'unit': '', 'data_type': 'string', 'default_threshold': 0, 'min_value': 0, 'max_value': 1, 'operators': ['==', '!='], 'sort_order': 1},
            {'resource_type_id': client_type.id, 'name': '客户端代理状态', 'code': 'client_agent_status', 'description': '客户端代理运行状态', 'unit': '', 'data_type': 'string', 'default_threshold': 0, 'min_value': 0, 'max_value': 1, 'operators': ['==', '!='], 'sort_order': 2},
            {'resource_type_id': client_type.id, 'name': '客户端响应时间', 'code': 'client_response_time', 'description': '客户端响应时间', 'unit': 'ms', 'data_type': 'float', 'default_threshold': 5000.0, 'min_value': 0.0, 'max_value': 60000.0, 'operators': ['>', '>=', '<', '<='], 'sort_order': 3},
            {'resource_type_id': client_type.id, 'name': '客户端最后心跳时间', 'code': 'client_last_heartbeat', 'description': '客户端最后心跳时间间隔', 'unit': 's', 'data_type': 'int', 'default_threshold': 300, 'min_value': 0, 'max_value': 86400, 'operators': ['>', '>=', '<', '<='], 'sort_order': 4},
            
            # 节点资源条目
            {'resource_type_id': node_type.id, 'name': '节点状态', 'code': 'node_status', 'description': '同步节点运行状态', 'unit': '', 'data_type': 'string', 'default_threshold': 0, 'min_value': 0, 'max_value': 1, 'operators': ['==', '!='], 'sort_order': 1},
            {'resource_type_id': node_type.id, 'name': '代理状态', 'code': 'agent_status', 'description': '节点代理运行状态', 'unit': '', 'data_type': 'string', 'default_threshold': 0, 'min_value': 0, 'max_value': 1, 'operators': ['==', '!='], 'sort_order': 2},
            {'resource_type_id': node_type.id, 'name': '任务执行数量', 'code': 'task_count', 'description': '当前执行的任务数量', 'unit': '个', 'data_type': 'int', 'default_threshold': 10, 'min_value': 0, 'max_value': 1000, 'operators': ['>', '>=', '<', '<='], 'sort_order': 3},
            {'resource_type_id': node_type.id, 'name': '节点最后心跳时间', 'code': 'node_last_heartbeat', 'description': '节点最后心跳时间间隔', 'unit': 's', 'data_type': 'int', 'default_threshold': 300, 'min_value': 0, 'max_value': 86400, 'operators': ['>', '>=', '<', '<='], 'sort_order': 4}
        ]
        
        for item_data in resource_items:
            resource_item = AlertResourceItem(**item_data)
            db.session.add(resource_item)
        
        db.session.commit()
        logger.info("告警资源条目初始化完成")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"初始化告警资源条目失败: {e}")
        raise


def init_alert_event_types():
    """初始化告警事件类型"""
    try:
        if AlertEventType.query.count() > 0:
            logger.info("告警事件类型已存在，跳过初始化")
            return
        
        event_types = [
            {'name': '用户资源', 'code': 'user', 'description': '用户相关的操作事件', 'category': 'user', 'icon': 'person', 'sort_order': 1},
            {'name': '存储资源', 'code': 'storage', 'description': '存储相关的操作事件', 'category': 'storage', 'icon': 'storage', 'sort_order': 2},
            {'name': '同步代理资源', 'code': 'agent', 'description': '同步代理相关的操作事件', 'category': 'agent', 'icon': 'hub', 'sort_order': 3},
            {'name': '客户端资源', 'code': 'client', 'description': '客户端相关的操作事件', 'category': 'client', 'icon': 'devices', 'sort_order': 4},
            {'name': '监控资源', 'code': 'monitor', 'description': '监控相关的操作事件', 'category': 'monitor', 'icon': 'monitor', 'sort_order': 5},
            {'name': '任务资源', 'code': 'task', 'description': '任务相关的操作事件', 'category': 'task', 'icon': 'assignment', 'sort_order': 6},
            {'name': '系统资源', 'code': 'system', 'description': '系统相关的操作事件', 'category': 'system', 'icon': 'computer', 'sort_order': 7},
            {'name': '节点资源', 'code': 'node', 'description': '节点相关的操作事件', 'category': 'node', 'icon': 'hub', 'sort_order': 8}
        ]
        
        for et_data in event_types:
            event_type = AlertEventType(**et_data)
            db.session.add(event_type)
        
        db.session.commit()
        logger.info("告警事件类型初始化完成")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"初始化告警事件类型失败: {e}")
        raise


def init_alert_event_actions():
    """初始化告警事件动作"""
    try:
        if AlertEventAction.query.count() > 0:
            logger.info("告警事件动作已存在，跳过初始化")
            return
        
        # 获取事件类型
        user_type = AlertEventType.query.filter_by(code='user').first()
        storage_type = AlertEventType.query.filter_by(code='storage').first()
        agent_type = AlertEventType.query.filter_by(code='agent').first()
        client_type = AlertEventType.query.filter_by(code='client').first()
        monitor_type = AlertEventType.query.filter_by(code='monitor').first()
        task_type = AlertEventType.query.filter_by(code='task').first()
        system_type = AlertEventType.query.filter_by(code='system').first()
        node_type = AlertEventType.query.filter_by(code='node').first()
        
        event_actions = [
            # 用户资源事件动作
            {'event_type_id': user_type.id, 'name': '用户登录', 'code': 'login', 'description': '用户登录系统', 'sort_order': 1},
            {'event_type_id': user_type.id, 'name': '用户登出', 'code': 'logout', 'description': '用户登出系统', 'sort_order': 2},
            {'event_type_id': user_type.id, 'name': '修改密码', 'code': 'change_password', 'description': '用户修改密码', 'sort_order': 3},
            {'event_type_id': user_type.id, 'name': '重置密码', 'code': 'reset_password', 'description': '用户重置密码', 'sort_order': 4},
            {'event_type_id': user_type.id, 'name': '修改邮箱', 'code': 'change_email', 'description': '用户修改邮箱', 'sort_order': 5},
            {'event_type_id': user_type.id, 'name': '修改个人信息', 'code': 'update_profile', 'description': '用户修改个人信息', 'sort_order': 6},
            {'event_type_id': user_type.id, 'name': '用户注册', 'code': 'register', 'description': '新用户注册', 'sort_order': 7},
            {'event_type_id': user_type.id, 'name': '删除用户', 'code': 'delete_user', 'description': '删除用户账户', 'sort_order': 8},
            {'event_type_id': user_type.id, 'name': '用户权限变更', 'code': 'change_permission', 'description': '用户权限变更', 'sort_order': 9},
            {'event_type_id': user_type.id, 'name': '用户锁定', 'code': 'lock_user', 'description': '用户账户被锁定', 'sort_order': 10},
            {'event_type_id': user_type.id, 'name': '用户解锁', 'code': 'unlock_user', 'description': '用户账户被解锁', 'sort_order': 11},
            
            # 存储资源事件动作
            {'event_type_id': storage_type.id, 'name': '添加存储', 'code': 'add_storage', 'description': '添加新的存储配置', 'sort_order': 1},
            {'event_type_id': storage_type.id, 'name': '删除存储', 'code': 'delete_storage', 'description': '删除存储配置', 'sort_order': 2},
            {'event_type_id': storage_type.id, 'name': '更新存储', 'code': 'update_storage', 'description': '更新存储配置', 'sort_order': 3},
            {'event_type_id': storage_type.id, 'name': '测试存储连通性', 'code': 'test_storage_connection', 'description': '测试存储连接状态', 'sort_order': 4},
            {'event_type_id': storage_type.id, 'name': '获取存储信息', 'code': 'get_storage_info', 'description': '获取存储详细信息', 'sort_order': 5},
            {'event_type_id': storage_type.id, 'name': '存储失联', 'code': 'storage_disconnected', 'description': '存储连接断开', 'sort_order': 6},
            {'event_type_id': storage_type.id, 'name': '存储恢复', 'code': 'storage_reconnected', 'description': '存储连接恢复', 'sort_order': 7},
            {'event_type_id': storage_type.id, 'name': '存储空间不足', 'code': 'storage_space_low', 'description': '存储空间不足警告', 'sort_order': 8},
            {'event_type_id': storage_type.id, 'name': '存储挂载', 'code': 'storage_mount', 'description': '存储挂载操作', 'sort_order': 9},
            {'event_type_id': storage_type.id, 'name': '存储卸载', 'code': 'storage_unmount', 'description': '存储卸载操作', 'sort_order': 10},
            {'event_type_id': storage_type.id, 'name': '存储同步', 'code': 'storage_sync', 'description': '存储同步操作', 'sort_order': 11},
            
            # 同步代理资源事件动作
            {'event_type_id': agent_type.id, 'name': '代理启动', 'code': 'agent_start', 'description': '同步代理启动', 'sort_order': 1},
            {'event_type_id': agent_type.id, 'name': '代理停止', 'code': 'agent_stop', 'description': '同步代理停止', 'sort_order': 2},
            {'event_type_id': agent_type.id, 'name': '代理重启', 'code': 'agent_restart', 'description': '同步代理重启', 'sort_order': 3},
            {'event_type_id': agent_type.id, 'name': '代理连接', 'code': 'agent_connect', 'description': '代理连接到服务器', 'sort_order': 4},
            {'event_type_id': agent_type.id, 'name': '代理断开', 'code': 'agent_disconnect', 'description': '代理与服务器断开连接', 'sort_order': 5},
            {'event_type_id': agent_type.id, 'name': '代理错误', 'code': 'agent_error', 'description': '代理运行错误', 'sort_order': 6},
            {'event_type_id': agent_type.id, 'name': '代理升级', 'code': 'agent_upgrade', 'description': '代理版本升级', 'sort_order': 7},
            {'event_type_id': agent_type.id, 'name': '代理配置更新', 'code': 'agent_config_update', 'description': '代理配置更新', 'sort_order': 8},
            {'event_type_id': agent_type.id, 'name': '代理心跳', 'code': 'agent_heartbeat', 'description': '代理心跳检测', 'sort_order': 9},
            
            # 客户端资源事件动作
            {'event_type_id': client_type.id, 'name': '客户端连接', 'code': 'client_connect', 'description': '客户端连接到系统', 'sort_order': 1},
            {'event_type_id': client_type.id, 'name': '客户端断开', 'code': 'client_disconnect', 'description': '客户端断开连接', 'sort_order': 2},
            {'event_type_id': client_type.id, 'name': '客户端错误', 'code': 'client_error', 'description': '客户端运行错误', 'sort_order': 3},
            {'event_type_id': client_type.id, 'name': '客户端超时', 'code': 'client_timeout', 'description': '客户端请求超时', 'sort_order': 4},
            {'event_type_id': client_type.id, 'name': '客户端认证失败', 'code': 'client_auth_failed', 'description': '客户端认证失败', 'sort_order': 5},
            {'event_type_id': client_type.id, 'name': '客户端添加', 'code': 'client_add', 'description': '添加新客户端', 'sort_order': 6},
            {'event_type_id': client_type.id, 'name': '客户端删除', 'code': 'client_delete', 'description': '删除客户端', 'sort_order': 7},
            {'event_type_id': client_type.id, 'name': '客户端更新', 'code': 'client_update', 'description': '更新客户端配置', 'sort_order': 8},
            {'event_type_id': client_type.id, 'name': '客户端代理安装', 'code': 'client_agent_install', 'description': '客户端代理安装', 'sort_order': 9},
            {'event_type_id': client_type.id, 'name': '客户端代理卸载', 'code': 'client_agent_uninstall', 'description': '客户端代理卸载', 'sort_order': 10},
            {'event_type_id': client_type.id, 'name': '客户端代理升级', 'code': 'client_agent_upgrade', 'description': '客户端代理升级', 'sort_order': 11},
            {'event_type_id': client_type.id, 'name': '客户端心跳', 'code': 'client_heartbeat', 'description': '客户端心跳检测', 'sort_order': 12},
            
            # 监控资源事件动作
            {'event_type_id': monitor_type.id, 'name': '监控数据收集', 'code': 'monitor_data_collect', 'description': '收集监控数据', 'sort_order': 1},
            {'event_type_id': monitor_type.id, 'name': '监控告警触发', 'code': 'monitor_alert_trigger', 'description': '监控告警触发', 'sort_order': 2},
            {'event_type_id': monitor_type.id, 'name': '监控告警恢复', 'code': 'monitor_alert_resolve', 'description': '监控告警恢复', 'sort_order': 3},
            {'event_type_id': monitor_type.id, 'name': '监控服务异常', 'code': 'monitor_service_error', 'description': '监控服务异常', 'sort_order': 4},
            {'event_type_id': monitor_type.id, 'name': '监控阈值设置', 'code': 'monitor_threshold_set', 'description': '设置监控阈值', 'sort_order': 5},
            {'event_type_id': monitor_type.id, 'name': '监控策略创建', 'code': 'monitor_policy_create', 'description': '创建监控策略', 'sort_order': 6},
            {'event_type_id': monitor_type.id, 'name': '监控策略更新', 'code': 'monitor_policy_update', 'description': '更新监控策略', 'sort_order': 7},
            {'event_type_id': monitor_type.id, 'name': '监控策略删除', 'code': 'monitor_policy_delete', 'description': '删除监控策略', 'sort_order': 8},
            
            # 任务资源事件动作
            {'event_type_id': task_type.id, 'name': '任务创建', 'code': 'task_create', 'description': '创建新的同步任务', 'sort_order': 1},
            {'event_type_id': task_type.id, 'name': '任务启动', 'code': 'task_start', 'description': '任务开始执行', 'sort_order': 2},
            {'event_type_id': task_type.id, 'name': '任务完成', 'code': 'task_complete', 'description': '任务执行完成', 'sort_order': 3},
            {'event_type_id': task_type.id, 'name': '任务失败', 'code': 'task_fail', 'description': '任务执行失败', 'sort_order': 4},
            {'event_type_id': task_type.id, 'name': '任务暂停', 'code': 'task_pause', 'description': '任务暂停执行', 'sort_order': 5},
            {'event_type_id': task_type.id, 'name': '任务恢复', 'code': 'task_resume', 'description': '任务恢复执行', 'sort_order': 6},
            {'event_type_id': task_type.id, 'name': '任务取消', 'code': 'task_cancel', 'description': '任务被取消', 'sort_order': 7},
            {'event_type_id': task_type.id, 'name': '任务删除', 'code': 'task_delete', 'description': '删除任务', 'sort_order': 8},
            {'event_type_id': task_type.id, 'name': '任务重试', 'code': 'task_retry', 'description': '任务重试执行', 'sort_order': 9},
            {'event_type_id': task_type.id, 'name': '任务分配', 'code': 'task_assign', 'description': '任务分配给节点', 'sort_order': 10},
            {'event_type_id': task_type.id, 'name': '任务进度更新', 'code': 'task_progress_update', 'description': '任务进度更新', 'sort_order': 11},
            {'event_type_id': task_type.id, 'name': '任务配置更新', 'code': 'task_config_update', 'description': '任务配置更新', 'sort_order': 12},
            
            # 系统资源事件动作
            {'event_type_id': system_type.id, 'name': '系统启动', 'code': 'system_start', 'description': '系统启动', 'sort_order': 1},
            {'event_type_id': system_type.id, 'name': '系统关闭', 'code': 'system_shutdown', 'description': '系统关闭', 'sort_order': 2},
            {'event_type_id': system_type.id, 'name': '系统重启', 'code': 'system_restart', 'description': '系统重启', 'sort_order': 3},
            {'event_type_id': system_type.id, 'name': '系统错误', 'code': 'system_error', 'description': '系统运行错误', 'sort_order': 4},
            {'event_type_id': system_type.id, 'name': '系统维护', 'code': 'system_maintenance', 'description': '系统维护操作', 'sort_order': 5},
            {'event_type_id': system_type.id, 'name': '配置更新', 'code': 'config_update', 'description': '系统配置更新', 'sort_order': 6},
            {'event_type_id': system_type.id, 'name': '数据库备份', 'code': 'database_backup', 'description': '数据库备份操作', 'sort_order': 7},
            {'event_type_id': system_type.id, 'name': '数据库恢复', 'code': 'database_restore', 'description': '数据库恢复操作', 'sort_order': 8},
            {'event_type_id': system_type.id, 'name': '日志清理', 'code': 'log_cleanup', 'description': '日志清理操作', 'sort_order': 9},
            {'event_type_id': system_type.id, 'name': '系统升级', 'code': 'system_upgrade', 'description': '系统升级操作', 'sort_order': 10},
            
            # 节点资源事件动作
            {'event_type_id': node_type.id, 'name': '节点添加', 'code': 'node_add', 'description': '添加新节点', 'sort_order': 1},
            {'event_type_id': node_type.id, 'name': '节点删除', 'code': 'node_delete', 'description': '删除节点', 'sort_order': 2},
            {'event_type_id': node_type.id, 'name': '节点更新', 'code': 'node_update', 'description': '更新节点配置', 'sort_order': 3},
            {'event_type_id': node_type.id, 'name': '节点连接', 'code': 'node_connect', 'description': '节点连接到系统', 'sort_order': 4},
            {'event_type_id': node_type.id, 'name': '节点断开', 'code': 'node_disconnect', 'description': '节点断开连接', 'sort_order': 5},
            {'event_type_id': node_type.id, 'name': '节点心跳', 'code': 'node_heartbeat', 'description': '节点心跳检测', 'sort_order': 6},
            {'event_type_id': node_type.id, 'name': '节点代理安装', 'code': 'node_agent_install', 'description': '节点代理安装', 'sort_order': 7},
            {'event_type_id': node_type.id, 'name': '节点代理卸载', 'code': 'node_agent_uninstall', 'description': '节点代理卸载', 'sort_order': 8},
            {'event_type_id': node_type.id, 'name': '节点代理升级', 'code': 'node_agent_upgrade', 'description': '节点代理升级', 'sort_order': 9},
            {'event_type_id': node_type.id, 'name': '节点分组变更', 'code': 'node_group_change', 'description': '节点分组变更', 'sort_order': 10}
        ]
        
        for action_data in event_actions:
            event_action = AlertEventAction(**action_data)
            db.session.add(event_action)
        
        db.session.commit()
        logger.info("告警事件动作初始化完成")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"初始化告警事件动作失败: {e}")
        raise


def init_alert_event_results():
    """初始化告警事件结果"""
    try:
        if AlertEventResult.query.count() > 0:
            logger.info("告警事件结果已存在，跳过初始化")
            return
        
        event_results = [
            {'name': '成功', 'code': 'success', 'description': '操作执行成功', 'color': 'success', 'sort_order': 1},
            {'name': '失败', 'code': 'failed', 'description': '操作执行失败', 'color': 'error', 'sort_order': 2},
            {'name': '超时', 'code': 'timeout', 'description': '操作执行超时', 'color': 'warning', 'sort_order': 3},
            {'name': '错误', 'code': 'error', 'description': '操作执行错误', 'color': 'error', 'sort_order': 4},
            {'name': '警告', 'code': 'warning', 'description': '操作执行警告', 'color': 'warning', 'sort_order': 5},
            {'name': '进行中', 'code': 'running', 'description': '操作正在执行中', 'color': 'info', 'sort_order': 6},
            {'name': '已取消', 'code': 'cancelled', 'description': '操作已被取消', 'color': 'info', 'sort_order': 7},
            {'name': '部分成功', 'code': 'partial_success', 'description': '操作部分成功', 'color': 'warning', 'sort_order': 8}
        ]
        
        for result_data in event_results:
            event_result = AlertEventResult(**result_data)
            db.session.add(event_result)
        
        db.session.commit()
        logger.info("告警事件结果初始化完成")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"初始化告警事件结果失败: {e}")
        raise


def init_all_alert_data():
    """初始化所有告警相关数据"""
    try:
        logger.info("开始初始化告警系统数据...")
        
        init_alert_resource_types()
        init_alert_resource_items()
        init_alert_event_types()
        init_alert_event_actions()
        init_alert_event_results()
        
        logger.info("告警系统数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化告警系统数据失败: {e}")
        raise


if __name__ == '__main__':
    init_all_alert_data()
