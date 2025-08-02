import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend import db
from backend.app.models import Client, AuditLog, MonitorData
from backend.app.notifications.services import NotificationService
from backend.app.utils.ssh_utils import SSHClient
from flask import g

logger = logging.getLogger(__name__)

class ClientService:
    """客户端服务类"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.heartbeat_timeout = 300  # 5分钟心跳超时
        
    def create_client(self, client_data: Dict[str, Any]) -> Client:
        """创建客户端"""
        try:
            client = Client(
                name=client_data['name'],
                ip_address=client_data['ip_address'],
                username=client_data['username'],
                auth_type=client_data['auth_type'],
                port=client_data.get('port', 22),
                password=client_data.get('password'),
                ssh_key=client_data.get('ssh_key'),
                description=client_data.get('description'),
                group=client_data.get('group', 'default'),
                tags=client_data.get('tags', ''),
                user_id=g.user.id
            )
            
            db.session.add(client)
            db.session.commit()
            
            # 发送创建成功通知
            self._send_client_notification(
                client,
                'created',
                f'客户端 {client.name} 已成功创建',
                {'ip_address': client.ip_address, 'auth_type': client.auth_type}
            )
            
            # 记录审计日志
            self._create_audit_log(
                user_id=g.user.id,
                action='create',
                resource_type='client',
                resource_id=client.id,
                details={'name': client.name, 'ip_address': client.ip_address}
            )
            
            logger.info(f"Client created: {client.id} - {client.name}")
            return client
            
        except Exception as e:
            # 发送创建失败通知
            self.notification_service.notify_client_error(
                user_id=g.user.id,
                client_name=client_data.get('name', 'Unknown'),
                error_message=f'创建客户端失败: {str(e)}'
            )
            logger.error(f"Failed to create client {client_data.get('name')}: {str(e)}")
            raise
    
    def update_client(self, client_id: str, client_data: Dict[str, Any]) -> Optional[Client]:
        """更新客户端"""
        client = Client.query.filter_by(id=client_id, user_id=g.user.id).first()
        if not client:
            return None
        
        try:
            # 记录原始值用于通知
            original_name = client.name
            original_ip = client.ip_address
            original_status = client.status
            
            # 更新客户端信息
            for key, value in client_data.items():
                if hasattr(client, key):
                    setattr(client, key, value)
            
            db.session.commit()
            
            # 发送更新成功通知
            changes = []
            if client_data.get('name') and client_data['name'] != original_name:
                changes.append(f'名称: {original_name} → {client.name}')
            if client_data.get('ip_address') and client_data['ip_address'] != original_ip:
                changes.append(f'IP地址: {original_ip} → {client.ip_address}')
            
            if changes:
                self._send_client_notification(
                    client,
                    'updated',
                    f'客户端 {client.name} 配置已更新',
                    {'changes': changes}
                )
            
            # 记录审计日志
            self._create_audit_log(
                user_id=g.user.id,
                action='update',
                resource_type='client',
                resource_id=client.id,
                details={'name': client.name, 'ip_address': client.ip_address, 'changes': changes}
            )
            
            logger.info(f"Client updated: {client_id} - {client.name}")
            return client
            
        except Exception as e:
            # 发送更新失败通知
            self.notification_service.notify_client_error(
                user_id=client.user_id,
                client_name=client.name,
                error_message=f'更新客户端配置失败: {str(e)}'
            )
            logger.error(f"Failed to update client {client_id}: {str(e)}")
            raise
    
    def delete_client(self, client_id: str) -> bool:
        """删除客户端"""
        client = Client.query.filter_by(id=client_id, user_id=g.user.id).first()
        if not client:
            return False
        
        try:
            # 记录客户端信息用于通知
            client_name = client.name
            client_ip = client.ip_address
            
            # 删除相关监控数据
            MonitorData.query.filter_by(client_id=client.id).delete()
            
            # 记录审计日志
            self._create_audit_log(
                user_id=g.user.id,
                action='delete',
                resource_type='client',
                resource_id=client.id,
                details={'name': client.name, 'ip_address': client.ip_address}
            )
            
            db.session.delete(client)
            db.session.commit()
            
            # 发送删除成功通知
            self.notification_service.create_notification(
                user_id=g.user.id,
                type='client_deleted',
                title=f'客户端已删除: {client_name}',
                content=f'客户端 {client_name} ({client_ip}) 已被删除，相关数据已清理。',
                level='info'
            )
            
            logger.info(f"Client deleted: {client_id} - {client_name}")
            return True
            
        except Exception as e:
            # 发送删除失败通知
            self.notification_service.notify_client_error(
                user_id=client.user_id,
                client_name=client.name,
                error_message=f'删除客户端失败: {str(e)}'
            )
            logger.error(f"Failed to delete client {client_id}: {str(e)}")
            raise
    
    def test_connection(self, client_id: str, send_notification: bool = True) -> Dict[str, Any]:
        """测试客户端连接"""
        client = Client.query.filter_by(id=client_id, user_id=g.user.id).first()
        if not client:
            return {'status': 'error', 'message': '客户端不存在'}
        
        try:
            with SSHClient(client=client) as ssh:
                # 连接成功
                client.status = 'online'
                client.last_seen = datetime.utcnow()
                db.session.commit()
                
                if send_notification:
                    self._send_client_notification(
                        client,
                        'connected',
                        f'客户端 {client.name} 连接测试成功'
                    )
                
                # 记录审计日志
                self._create_audit_log(
                    user_id=client.user_id,
                    action='test_connection',
                    resource_type='client',
                    resource_id=client.id,
                    details={'status': 'success'}
                )
                
                return {'status': 'success', 'message': '连接测试成功'}
                
        except Exception as e:
            # 连接失败
            client.status = 'offline'
            db.session.commit()
            
            error_msg = f'连接测试失败: {str(e)}'
            
            if send_notification:
                self.notification_service.notify_client_disconnected(
                    user_id=client.user_id,
                    client_name=client.name,
                    reason=error_msg
                )
            
            # 记录审计日志
            self._create_audit_log(
                user_id=client.user_id,
                action='test_connection',
                resource_type='client',
                resource_id=client.id,
                details={'status': 'failed', 'error': str(e)}
            )
            
            logger.error(f"Client connection test failed: {client_id} - {str(e)}")
            return {'status': 'error', 'message': error_msg}
    
    def install_agent(self, client_id: str, install_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """安装Agent"""
        client = Client.query.filter_by(id=client_id, user_id=g.user.id).first()
        if not client:
            return {'status': 'error', 'message': '客户端不存在'}
        
        try:
            # 更新状态为安装中
            client.agent_status = 'installing'
            db.session.commit()
            
            # 发送安装开始通知
            self.notification_service.create_notification(
                user_id=client.user_id,
                type='client_agent_installing',
                title=f'Agent安装开始: {client.name}',
                content=f'正在为客户端 {client.name} 安装Agent...',
                level='info'
            )
            
            # 这里应该包含实际的安装逻辑
            # ... 安装逻辑 ...
            
            # 模拟安装成功
            client.agent_status = 'running'
            client.agent_version = '1.0.0'
            db.session.commit()
            
            # 发送安装成功通知
            self.notification_service.create_notification(
                user_id=client.user_id,
                type='client_agent_installed',
                title=f'Agent安装成功: {client.name}',
                content=f'客户端 {client.name} 的Agent已成功安装并运行。\n版本: {client.agent_version}',
                level='success'
            )
            
            logger.info(f"Agent installed successfully: {client_id}")
            return {'status': 'success', 'message': 'Agent安装成功'}
            
        except Exception as e:
            # 安装失败
            client.agent_status = 'install_error'
            db.session.commit()
            
            error_msg = f'Agent安装失败: {str(e)}'
            
            # 发送安装失败通知
            self.notification_service.notify_client_error(
                user_id=client.user_id,
                client_name=client.name,
                error_message=error_msg
            )
            
            logger.error(f"Agent installation failed: {client_id} - {str(e)}")
            return {'status': 'error', 'message': error_msg}
    
    def uninstall_agent(self, client_id: str) -> Dict[str, Any]:
        """卸载Agent"""
        client = Client.query.filter_by(id=client_id, user_id=g.user.id).first()
        if not client:
            return {'status': 'error', 'message': '客户端不存在'}
        
        try:
            # 更新状态为卸载中
            client.agent_status = 'uninstalling'
            db.session.commit()
            
            # 发送卸载开始通知
            self.notification_service.create_notification(
                user_id=client.user_id,
                type='client_agent_uninstalling',
                title=f'Agent卸载开始: {client.name}',
                content=f'正在卸载客户端 {client.name} 的Agent...',
                level='info'
            )
            
            # 这里应该包含实际的卸载逻辑
            # ... 卸载逻辑 ...
            
            # 模拟卸载成功
            client.agent_status = 'not_installed'
            client.agent_version = None
            db.session.commit()
            
            # 发送卸载成功通知
            self.notification_service.create_notification(
                user_id=client.user_id,
                type='client_agent_uninstalled',
                title=f'Agent卸载成功: {client.name}',
                content=f'客户端 {client.name} 的Agent已成功卸载。',
                level='info'
            )
            
            logger.info(f"Agent uninstalled successfully: {client_id}")
            return {'status': 'success', 'message': 'Agent卸载成功'}
            
        except Exception as e:
            # 卸载失败
            client.agent_status = 'uninstall_error'
            db.session.commit()
            
            error_msg = f'Agent卸载失败: {str(e)}'
            
            # 发送卸载失败通知
            self.notification_service.notify_client_error(
                user_id=client.user_id,
                client_name=client.name,
                error_message=error_msg
            )
            
            logger.error(f"Agent uninstallation failed: {client_id} - {str(e)}")
            return {'status': 'error', 'message': error_msg}
    
    def upgrade_agent(self, client_id: str, version: str) -> Dict[str, Any]:
        """升级Agent"""
        client = Client.query.filter_by(id=client_id, user_id=g.user.id).first()
        if not client:
            return {'status': 'error', 'message': '客户端不存在'}
        
        try:
            old_version = client.agent_version
            
            # 更新状态为升级中
            client.agent_status = 'upgrading'
            db.session.commit()
            
            # 发送升级开始通知
            self.notification_service.create_notification(
                user_id=client.user_id,
                type='client_agent_upgrading',
                title=f'Agent升级开始: {client.name}',
                content=f'正在升级客户端 {client.name} 的Agent...\n当前版本: {old_version}\n目标版本: {version}',
                level='info'
            )
            
            # 这里应该包含实际的升级逻辑
            # ... 升级逻辑 ...
            
            # 模拟升级成功
            client.agent_status = 'running'
            client.agent_version = version
            db.session.commit()
            
            # 发送升级成功通知
            self.notification_service.notify_client_version_updated(
                user_id=client.user_id,
                client_name=client.name,
                old_version=old_version,
                new_version=version
            )
            
            logger.info(f"Agent upgraded successfully: {client_id} - {old_version} -> {version}")
            return {'status': 'success', 'message': 'Agent升级成功'}
            
        except Exception as e:
            # 升级失败
            client.agent_status = 'error'
            db.session.commit()
            
            error_msg = f'Agent升级失败: {str(e)}'
            
            # 发送升级失败通知
            self.notification_service.notify_client_error(
                user_id=client.user_id,
                client_name=client.name,
                error_message=error_msg
            )
            
            logger.error(f"Agent upgrade failed: {client_id} - {str(e)}")
            return {'status': 'error', 'message': error_msg}
    
    def handle_client_heartbeat(self, client_id: str, user_id: str, resource_info: Dict[str, Any] = None):
        """处理客户端心跳"""
        try:
            now = datetime.utcnow()
            client = Client.query.filter_by(id=client_id, user_id=user_id).first()
            
            if not client:
                # 首次上线自动注册
                client = Client(
                    id=client_id,
                    user_id=user_id,
                    name=resource_info.get('name', f'Agent-{client_id[:8]}'),
                    ip_address=resource_info.get('ip_address', ''),
                    agent_status='running',
                    last_seen=now
                )
                db.session.add(client)
                
                # 发送客户端注册通知
                self.notification_service.notify_client_registered(
                    user_id=user_id,
                    client_name=client.name,
                    version=resource_info.get('agent_version')
                )
                
            else:
                previous_status = client.agent_status
                client.agent_status = 'running'
                client.last_seen = now
                
                # 如果客户端从离线状态恢复
                if previous_status != 'running':
                    self.notification_service.notify_client_connected(
                        user_id=user_id,
                        client_name=client.name,
                        client_ip=client.ip_address
                    )
                
                # 更新资源信息
                if resource_info:
                    for key, value in resource_info.items():
                        if hasattr(client, key):
                            setattr(client, key, value)
            
            db.session.commit()
            logger.debug(f"Client heartbeat processed: {client_id}")
            
        except Exception as e:
            logger.error(f"处理客户端心跳失败: {client_id} - {str(e)}")
    
    def check_client_timeouts(self):
        """检查客户端心跳超时"""
        try:
            current_time = datetime.utcnow()
            timeout_threshold = current_time - timedelta(seconds=self.heartbeat_timeout)
            
            # 查找心跳超时的在线客户端
            timeout_clients = Client.query.filter(
                Client.agent_status == 'running',
                Client.last_seen < timeout_threshold
            ).all()
            
            for client in timeout_clients:
                # 更新状态为离线
                client.agent_status = 'offline'
                
                # 发送心跳超时通知
                time_diff = current_time - client.last_seen
                self.notification_service.create_notification(
                    user_id=client.user_id,
                    type='client_heartbeat_timeout',
                    title=f'客户端心跳超时: {client.name}',
                    content=f'客户端 {client.name} 心跳超时，已自动标记为离线。\n'
                           f'最后心跳时间: {client.last_seen.strftime("%Y-%m-%d %H:%M:%S")}\n'
                           f'超时时长: {int(time_diff.total_seconds())} 秒\n'
                           f'IP地址: {client.ip_address}',
                    level='warning'
                )
                
                logger.warning(f"Client {client.id} ({client.name}) marked as offline due to heartbeat timeout")
            
            if timeout_clients:
                db.session.commit()
                
        except Exception as e:
            logger.error(f"检查客户端超时失败: {str(e)}")
    
    def monitor_client_resources(self, client_id: str, resource_data: Dict[str, Any]):
        """监控客户端资源使用情况"""
        try:
            client = Client.query.get(client_id)
            if not client:
                return
            
            # 检查CPU使用率警告
            cpu_usage = resource_data.get('cpu', {}).get('usage', 0)
            if cpu_usage > 85:
                self.notification_service.create_notification(
                    user_id=client.user_id,
                    type='client_resource_warning',
                    title=f'客户端资源警告: {client.name}',
                    content=f'客户端 {client.name} 的CPU使用率已达到 {cpu_usage:.1f}%，请及时处理。\nIP地址: {client.ip_address}',
                    level='warning'
                )
            
            # 检查内存使用率警告
            memory_usage = resource_data.get('memory', {}).get('usage_percent', 0)
            if memory_usage > 85:
                self.notification_service.create_notification(
                    user_id=client.user_id,
                    type='client_resource_warning',
                    title=f'客户端资源警告: {client.name}',
                    content=f'客户端 {client.name} 的内存使用率已达到 {memory_usage:.1f}%，请及时处理。\nIP地址: {client.ip_address}',
                    level='warning'
                )
            
            # 检查磁盘使用率警告
            disk_data = resource_data.get('disk', [])
            for disk in disk_data:
                if isinstance(disk, dict) and disk.get('usage_percent', 0) > 85:
                    self.notification_service.create_notification(
                        user_id=client.user_id,
                        type='client_resource_warning',
                        title=f'客户端磁盘警告: {client.name}',
                        content=f'客户端 {client.name} 的磁盘 {disk.get("mount", "/")} 使用率已达到 {disk["usage_percent"]:.1f}%，请及时处理。\nIP地址: {client.ip_address}',
                        level='warning'
                    )
                    
        except Exception as e:
            logger.error(f"监控客户端资源失败: {client_id} - {str(e)}")
    
    # =============== 辅助方法 ===============
    
    def _send_client_notification(self, client, operation_type, message, details=None):
        """发送客户端操作通知"""
        try:
            if operation_type == 'created':
                self.notification_service.create_notification(
                    user_id=client.user_id,
                    type='client_created',
                    title=f'客户端创建成功: {client.name}',
                    content=f'客户端 {client.name} 已成功创建并配置。\nIP地址: {client.ip_address}',
                    level='success'
                )
            elif operation_type == 'updated':
                changes_text = '\n'.join(details.get('changes', []))
                self.notification_service.create_notification(
                    user_id=client.user_id,
                    type='client_updated',
                    title=f'客户端配置更新: {client.name}',
                    content=f'{message}\n变更详情: {changes_text}',
                    level='info'
                )
            elif operation_type == 'connected':
                self.notification_service.notify_client_connected(
                    user_id=client.user_id,
                    client_name=client.name,
                    client_ip=client.ip_address
                )
            elif operation_type == 'disconnected':
                self.notification_service.notify_client_disconnected(
                    user_id=client.user_id,
                    client_name=client.name,
                    reason=details.get('reason', '连接断开')
                )
                
        except Exception as e:
            logger.error(f"发送客户端通知失败: {str(e)}")
    
    def _create_audit_log(self, user_id, action, resource_type, resource_id, details):
        """创建审计日志"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"创建审计日志失败: {str(e)}")