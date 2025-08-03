import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import and_, or_, desc
from backend import db
from backend.app.models.alert import (
    AlertPolicy, NotificationChannel, NotificationTarget, AlertInstance
)
from backend.app.models.client import Client
from backend.app.models.node import Node
from backend.app.models.user import User
from backend.app.notifications.services import NotificationService

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务类"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def get_policies(self, user_id: str, page: int = 1, per_page: int = 12,
                    policy_type: str = '', level: str = '', enabled: str = '', keyword: str = '') -> Dict[str, Any]:
        """获取告警策略列表"""
        query = AlertPolicy.query.filter(AlertPolicy.user_id == user_id)
        
        # 应用过滤器
        if policy_type:
            query = query.filter(AlertPolicy.policy_type == policy_type)
        if level:
            query = query.filter(AlertPolicy.level == level)
        if enabled:
            enabled_bool = enabled.lower() == 'true'
            query = query.filter(AlertPolicy.enabled == enabled_bool)
        if keyword:
            query = query.filter(
                or_(
                    AlertPolicy.name.contains(keyword),
                    AlertPolicy.description.contains(keyword)
                )
            )
        
        # 分页
        total = query.count()
        policies = query.order_by(desc(AlertPolicy.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'policies': [policy.to_dict() for policy in policies],
            'total': total,
            'current_page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    
    def create_policy(self, data: Dict[str, Any]) -> AlertPolicy:
        """创建告警策略"""
        # 验证数据
        self._validate_policy_data(data)
        
        # 创建策略
        policy = AlertPolicy(
            name=data['name'],
            description=data.get('description', ''),
            level=data.get('level', 'warning'),
            enabled=data.get('enabled', True),
            policy_type=data['policy_type'],
            resource_type=data.get('resource_type'),
            monitored_resources=data.get('monitored_resources', []),
            alert_items=data.get('alert_items', []),
            trigger_rules=data.get('trigger_rules', {}),
            event_type=data.get('event_type'),
            event_actions=data.get('event_actions', []),
            event_results=data.get('event_results', []),
            notification_targets=data.get('notification_targets', []),
            user_id=data['user_id']
        )
            
        db.session.add(policy)
        db.session.commit()
            
        logger.info(f"Alert policy created: {policy.id}")
        return policy
            
    def get_policy(self, policy_id: str, user_id: str) -> AlertPolicy:
        """获取告警策略详情"""
        policy = AlertPolicy.query.filter(
            and_(AlertPolicy.id == policy_id, AlertPolicy.user_id == user_id)
        ).first()
        
        if not policy:
            raise ValueError("告警策略不存在")
        
        return policy
    
    def update_policy(self, policy_id: str, user_id: str, data: Dict[str, Any]) -> AlertPolicy:
        """更新告警策略"""
        policy = self.get_policy(policy_id, user_id)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
            
            policy.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Alert policy updated: {policy_id}")
            return policy
            
    def delete_policy(self, policy_id: str, user_id: str) -> None:
        """删除告警策略"""
        policy = self.get_policy(policy_id, user_id)
        db.session.delete(policy)
        db.session.commit()
            
        logger.info(f"Alert policy deleted: {policy_id}")
    
    def toggle_policy(self, policy_id: str, user_id: str) -> AlertPolicy:
        """切换告警策略启用状态"""
        policy = self.get_policy(policy_id, user_id)
        policy.enabled = not policy.enabled
        policy.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Alert policy toggled: {policy_id} -> {policy.enabled}")
        return policy
    
    def test_policy(self, policy_id: str, user_id: str) -> Dict[str, Any]:
        """测试告警策略"""
        policy = self.get_policy(policy_id, user_id)
        
        # 模拟告警触发
        test_instance = AlertInstance(
            policy_id=policy.id,
            alert_name=f"测试告警 - {policy.name}",
            severity=policy.level,
            status='firing',
            metric_name='test_metric',
            current_value=100.0,
            threshold_value=80.0,
            labels={'test': 'true'},
            annotations={'description': '这是一个测试告警'},
            fingerprint=f"test_{policy.id}_{datetime.utcnow().timestamp()}",
            starts_at=datetime.utcnow()
        )
        
        db.session.add(test_instance)
        db.session.commit()
            
        # 发送测试通知
        self._send_notifications(policy, test_instance)
        
        return {
            'success': True,
            'message': '测试告警已触发',
            'instance_id': test_instance.id
        }

    def get_alert_statistics(self, time_range: str) -> Dict[str, Any]:
        """获取告警统计信息"""
        try:
            # 解析时间范围
            time_range = time_range.lower()
            if time_range == '24h':
                start_time = datetime.now() - timedelta(hours=24)
                end_time = datetime.now()
            elif time_range == '7d':
                start_time = datetime.now() - timedelta(days=7)
                end_time = datetime.now()
            elif time_range == '30d':
                start_time = datetime.now() - timedelta(days=30)
                end_time = datetime.now()
            else:
                raise ValueError(f"Invalid time range: {time_range}")
            
            # 获取告警统计数据
            stats = {
                'total_alerts': AlertInstance.query.filter(
                    AlertInstance.created_at >= start_time,
                    AlertInstance.created_at <= end_time
                ).count(),
                'active_alerts': AlertInstance.query.filter(
                    AlertInstance.created_at >= start_time,
                    AlertInstance.created_at <= end_time,
                    AlertInstance.status == 'active'
                ).count(),
                'resolved_alerts': AlertInstance.query.filter(
                    AlertInstance.created_at >= start_time,
                    AlertInstance.created_at <= end_time,
                    AlertInstance.status == 'resolved'
                ).count(),
                'suppressed_alerts': AlertInstance.query.filter(
                    AlertInstance.created_at >= start_time, 
                    AlertInstance.created_at <= end_time,
                    AlertInstance.status == 'suppressed'
                ).count(),
                'firing_alerts': AlertInstance.query.filter(
                    AlertInstance.created_at >= start_time,
                    AlertInstance.created_at <= end_time,
                    AlertInstance.status == 'firing'
                ).count(),
                'alert_types': {
                    'cpu_high': AlertInstance.query.filter(
                        AlertInstance.created_at >= start_time,
                        AlertInstance.created_at <= end_time,
                        AlertInstance.alert_type == 'cpu_high'
                    ).count(),
                    'memory_high': AlertInstance.query.filter(
                        AlertInstance.created_at >= start_time,
                        AlertInstance.created_at <= end_time,   
                        AlertInstance.alert_type == 'memory_high'
                    ).count(),
                    'disk_high': AlertInstance.query.filter(
                        AlertInstance.created_at >= start_time,
                        AlertInstance.created_at <= end_time,
                        AlertInstance.alert_type == 'disk_high'
                    ).count(),
                    'load_high': AlertInstance.query.filter(
                        AlertInstance.created_at >= start_time,
                        AlertInstance.created_at <= end_time,
                        AlertInstance.alert_type == 'load_high'
                    ).count(),
                    'network_high': AlertInstance.query.filter(
                        AlertInstance.created_at >= start_time,
                        AlertInstance.created_at <= end_time,
                        AlertInstance.alert_type == 'network_high'
                    ).count()
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {str(e)}")
            return {}

    def get_channels(self, user_id: str) -> List[Dict[str, Any]]:
        """获取通知渠道列表"""
        channels = NotificationChannel.query.filter(NotificationChannel.user_id == user_id).all()
        return [channel.to_dict() for channel in channels]
    
    def create_channel(self, data: Dict[str, Any]) -> NotificationChannel:
        """创建通知渠道"""
        # 验证数据
        self._validate_channel_data(data)
        
        # 如果设置为默认，先取消其他默认渠道
        if data.get('is_default', False):
            NotificationChannel.query.filter(
                and_(NotificationChannel.user_id == data['user_id'], NotificationChannel.is_default == True)
            ).update({'is_default': False})
        
            channel = NotificationChannel(
            name=data['name'],
            channel_type=data['channel_type'],
            enabled=data.get('enabled', True),
            config=data['config'],
            retry_count=data.get('retry_count', 3),
            rate_limit=data.get('rate_limit', 100),
            timeout=data.get('timeout', 30),
            is_default=data.get('is_default', False),
            user_id=data['user_id']
            )
            
            db.session.add(channel)
            db.session.commit()
            
            logger.info(f"Notification channel created: {channel.id}")
            return channel
            
    def update_channel(self, channel_id: str, user_id: str, data: Dict[str, Any]) -> NotificationChannel:
        """更新通知渠道"""
        channel = NotificationChannel.query.filter(
            and_(NotificationChannel.id == channel_id, NotificationChannel.user_id == user_id)
        ).first()
        
        if not channel:
            raise ValueError("通知渠道不存在")
        
        # 更新字段
        for key, value in data.items():
            if hasattr(channel, key):
                setattr(channel, key, value)
        
        # 如果设置为默认，先取消其他默认渠道
        if data.get('is_default', False):
            NotificationChannel.query.filter(
                and_(
                    NotificationChannel.user_id == user_id,
                    NotificationChannel.is_default == True,
                    NotificationChannel.id != channel_id
                )
            ).update({'is_default': False})
        
        channel.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Notification channel updated: {channel_id}")
        return channel
    
    def delete_channel(self, channel_id: str, user_id: str) -> None:
        """删除通知渠道"""
        channel = NotificationChannel.query.filter(
            and_(NotificationChannel.id == channel_id, NotificationChannel.user_id == user_id)
        ).first()
        
        if not channel:
            raise ValueError("通知渠道不存在")
        
        db.session.delete(channel)
        db.session.commit()
        
        logger.info(f"Notification channel deleted: {channel_id}")
    
    def get_targets(self, user_id: str) -> List[Dict[str, Any]]:
        """获取通知对象列表"""
        targets = NotificationTarget.query.filter(NotificationTarget.user_id == user_id).all()
        return [target.to_dict() for target in targets]
    
    def create_target(self, data: Dict[str, Any]) -> NotificationTarget:
        """创建通知对象"""
        # 验证数据
        self._validate_target_data(data)
        
        target = NotificationTarget(
            name=data['name'],
            enabled=data.get('enabled', True),
            description=data.get('description', ''),
            alert_policies=data.get('alert_policies', []),
            channels=data.get('channels', []),
            target_type=data['target_type'],
            target_config=data['target_config'],
            user_id=data['user_id']
        )
            
        db.session.add(target)
        db.session.commit()
            
        logger.info(f"Notification target created: {target.id}")
        return target
            
    def update_target(self, target_id: str, user_id: str, data: Dict[str, Any]) -> NotificationTarget:
        """更新通知对象"""
        target = NotificationTarget.query.filter(
            and_(NotificationTarget.id == target_id, NotificationTarget.user_id == user_id)
        ).first()
        
        if not target:
            raise ValueError("通知对象不存在")
        
        # 更新字段
        for key, value in data.items():
            if hasattr(target, key):
                setattr(target, key, value)
        
        target.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Notification target updated: {target_id}")
        return target
    
    def delete_target(self, target_id: str, user_id: str) -> None:
        """删除通知对象"""
        target = NotificationTarget.query.filter(
            and_(NotificationTarget.id == target_id, NotificationTarget.user_id == user_id)
        ).first()
        
        if not target:
            raise ValueError("通知对象不存在")
        
        db.session.delete(target)
        db.session.commit()
        
        logger.info(f"Notification target deleted: {target_id}")
    
    def get_instances(self, user_id: str, page: int = 1, per_page: int = 20,
                     status: str = '', severity: str = '') -> Dict[str, Any]:
        """获取告警实例列表"""
        # 获取用户的策略ID
        policy_ids = [p.id for p in AlertPolicy.query.filter(AlertPolicy.user_id == user_id).all()]
        
        query = AlertInstance.query.filter(AlertInstance.policy_id.in_(policy_ids))
        
        # 应用过滤器
        if status:
            query = query.filter(AlertInstance.status == status)
        if severity:
            query = query.filter(AlertInstance.severity == severity)
        
        # 分页
        total = query.count()
        instances = query.order_by(desc(AlertInstance.starts_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'instances': [instance.to_dict() for instance in instances],
            'total': total,
            'current_page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    
    def resolve_instance(self, instance_id: str, user_id: str) -> None:
        """解决告警实例"""
        # 获取用户策略ID
        policy_ids = [p.id for p in AlertPolicy.query.filter(AlertPolicy.user_id == user_id).all()]
        
        instance = AlertInstance.query.filter(
            and_(AlertInstance.id == instance_id, AlertInstance.policy_id.in_(policy_ids))
        ).first()
        
        if not instance:
            raise ValueError("告警实例不存在")
        
        instance.status = 'resolved'
        instance.resolved_at = datetime.utcnow()
        instance.ends_at = datetime.utcnow()
        db.session.commit()
            
        logger.info(f"Alert instance resolved: {instance_id}")
    
    def get_monitorable_resources(self, user_id: str) -> Dict[str, Any]:
        """获取可监控的资源列表"""
        resources = {
            'nodes': [],
            'clients': [],
            'system': []
        }
        
        # 获取节点
        nodes = Node.query.filter(Node.user_id == user_id).all()
        resources['nodes'] = [{'id': node.id, 'name': node.name} for node in nodes]
        
        # 获取客户端
        clients = Client.query.filter(Client.user_id == user_id).all()
        resources['clients'] = [{'id': client.id, 'name': client.name} for client in clients]
        
        # 系统资源
        resources['system'] = [
            {'id': 'cpu', 'name': 'CPU'},
            {'id': 'memory', 'name': '内存'},
            {'id': 'disk', 'name': '磁盘'},
            {'id': 'network', 'name': '网络'}
        ]
        
        return resources
    
    def get_monitorable_events(self) -> Dict[str, Any]:
        """获取可监控的事件列表"""
        events = {
            'storage': [
                {'id': 'create', 'name': '创建'},
                {'id': 'delete', 'name': '删除'},
                {'id': 'get', 'name': '获取'},
                {'id': 'update', 'name': '更新'}
            ],
            'client': [
                {'id': 'connect', 'name': '连接'},
                {'id': 'disconnect', 'name': '断开'},
                {'id': 'error', 'name': '错误'}
            ],
            'proxy': [
                {'id': 'start', 'name': '启动'},
                {'id': 'stop', 'name': '停止'},
                {'id': 'restart', 'name': '重启'},
                {'id': 'error', 'name': '错误'}
            ]
        }
        
        return {
            'events': events,
            'results': [
                {'id': 'success', 'name': '成功'},
                {'id': 'failed', 'name': '失败'},
                {'id': 'timeout', 'name': '超时'},
                {'id': 'error', 'name': '错误'},
                {'id': 'warning', 'name': '警告'}
            ]
        }
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """获取告警策略模板"""
        templates = [
            {
                'id': 'cpu_high',
                'name': 'CPU使用率过高',
                'policy_type': 'resource',
                'description': '当CPU使用率超过阈值时触发告警',
                'template': {
                    'resource_type': 'system',
                    'alert_items': ['cpu'],
                    'trigger_rules': {
                        'cpu': {
                            'operator': '>',
                            'threshold': 80,
                            'duration': 300
                        }
                    },
                    'level': 'warning'
                }
            },
            {
                'id': 'memory_high',
                'name': '内存使用率过高',
                'policy_type': 'resource',
                'description': '当内存使用率超过阈值时触发告警',
                'template': {
                    'resource_type': 'system',
                    'alert_items': ['memory'],
                    'trigger_rules': {
                        'memory': {
                            'operator': '>',
                            'threshold': 85,
                            'duration': 300
                        }
                    },
                    'level': 'warning'
                }
            },
            {
                'id': 'disk_space_low',
                'name': '磁盘空间不足',
                'policy_type': 'resource',
                'description': '当磁盘使用率超过阈值时触发告警',
                'template': {
                    'resource_type': 'system',
                    'alert_items': ['disk'],
                    'trigger_rules': {
                        'disk': {
                            'operator': '>',
                            'threshold': 90,
                            'duration': 300
                        }
                    },
                    'level': 'critical'
                }
            },
            {
                'id': 'storage_error',
                'name': '存储访问错误',
                'policy_type': 'event',
                'description': '当存储访问出现错误时触发告警',
                'template': {
                    'event_type': 'storage',
                    'event_actions': ['create', 'delete', 'update'],
                    'event_results': ['failed', 'error'],
                    'level': 'error'
                }
            },
            {
                'id': 'client_connection_failed',
                'name': '客户端连接失败',
                'policy_type': 'event',
                'description': '当客户端连接失败时触发告警',
                'template': {
                    'event_type': 'client',
                    'event_actions': ['connect'],
                    'event_results': ['failed', 'timeout'],
                    'level': 'warning'
                }
            }
        ]
        
        return templates
    
    def _validate_policy_data(self, data: Dict[str, Any]) -> None:
        """验证告警策略数据"""
        required_fields = ['name', 'policy_type', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填字段: {field}")
        
        if data['policy_type'] == 'resource':
            if not data.get('resource_type'):
                raise ValueError("资源告警必须指定资源类型")
            if not data.get('alert_items'):
                raise ValueError("资源告警必须指定报警条目")
            if not data.get('trigger_rules'):
                raise ValueError("资源告警必须指定触发规则")
        elif data['policy_type'] == 'event':
            if not data.get('event_type'):
                raise ValueError("事件告警必须指定事件类型")
            if not data.get('event_actions'):
                raise ValueError("事件告警必须指定事件动作")
            if not data.get('event_results'):
                raise ValueError("事件告警必须指定事件结果")
    
    def _validate_channel_data(self, data: Dict[str, Any]) -> None:
        """验证通知渠道数据"""
        required_fields = ['name', 'channel_type', 'config', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填字段: {field}")
        
        # 验证渠道配置
        channel_type = data['channel_type']
        config = data['config']
        
        if channel_type == 'email':
            if not config.get('smtp_server') or not config.get('smtp_port'):
                raise ValueError("邮件渠道必须配置SMTP服务器")
            if not config.get('username') or not config.get('password'):
                raise ValueError("邮件渠道必须配置用户名和密码")
        elif channel_type == 'sms':
            if not config.get('api_key') or not config.get('secret'):
                raise ValueError("短信渠道必须配置API密钥")
        elif channel_type == 'webhook':
            if not config.get('url'):
                raise ValueError("WebHook渠道必须配置URL")
        elif channel_type in ['dingtalk', 'slack']:
            if not config.get('webhook_url'):
                raise ValueError(f"{channel_type}渠道必须配置WebHook URL")
    
    def _validate_target_data(self, data: Dict[str, Any]) -> None:
        """验证通知对象数据"""
        required_fields = ['name', 'target_type', 'target_config', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填字段: {field}")
        
        # 验证目标配置
        target_type = data['target_type']
        config = data['target_config']
        
        if target_type == 'email':
            if not config.get('email'):
                raise ValueError("邮件通知对象必须配置邮箱地址")
        elif target_type == 'sms':
            if not config.get('phone'):
                raise ValueError("短信通知对象必须配置手机号码")
        elif target_type == 'webhook':
            if not config.get('url'):
                raise ValueError("WebHook通知对象必须配置URL")
    
    def _send_notifications(self, policy: AlertPolicy, instance: AlertInstance) -> None:
        """发送通知"""
        if not policy.notification_targets:
            return
        
        # 获取通知对象
        targets = NotificationTarget.query.filter(
            NotificationTarget.id.in_(policy.notification_targets)
        ).all()
        
        for target in targets:
            if not target.enabled:
                continue
            
            # 获取通知渠道
            if not target.channels:
                continue
            
            channels = NotificationChannel.query.filter(
                NotificationChannel.id.in_(target.channels)
            ).all()
            
            for channel in channels:
                if not channel.enabled:
                    continue
                
                try:
                    self._send_notification(channel, target, instance)
                except Exception as e:
                    logger.error(f"发送通知失败: {e}")
    
    def _send_notification(self, channel: NotificationChannel, target: NotificationTarget, instance: AlertInstance) -> None:
        """发送单个通知"""
        message = {
            'title': f"告警: {instance.alert_name}",
            'content': f"告警级别: {instance.severity}\n当前值: {instance.current_value}\n阈值: {instance.threshold_value}",
            'timestamp': instance.starts_at.isoformat(),
            'labels': instance.labels or {},
            'annotations': instance.annotations or {}
        }
        
        # 根据渠道类型发送通知
        if channel.channel_type == 'email':
            self._send_email_notification(channel, target, message)
        elif channel.channel_type == 'sms':
            self._send_sms_notification(channel, target, message)
        elif channel.channel_type == 'webhook':
            self._send_webhook_notification(channel, target, message)
        elif channel.channel_type in ['dingtalk', 'slack']:
            self._send_webhook_notification(channel, target, message)
    
    def _send_email_notification(self, channel: NotificationChannel, target: NotificationTarget, message: Dict[str, Any]) -> None:
        """发送邮件通知"""
        # 使用现有的通知服务
        self.notification_service.send_email_notification(
            to_email=target.target_config.get('email'),
            subject=message['title'],
            content=message['content'],
            smtp_config=channel.config
        )
    
    def _send_sms_notification(self, channel: NotificationChannel, target: NotificationTarget, message: Dict[str, Any]) -> None:
        """发送短信通知"""
        # 实现短信发送逻辑
        logger.info(f"发送短信通知到 {target.target_config.get('phone')}: {message['content']}")
    
    def _send_webhook_notification(self, channel: NotificationChannel, target: NotificationTarget, message: Dict[str, Any]) -> None:
        """发送WebHook通知"""
        # 实现WebHook发送逻辑
        logger.info(f"发送WebHook通知到 {channel.config.get('url')}: {message}")