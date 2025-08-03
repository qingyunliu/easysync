import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import and_, or_, desc
from backend import db
from backend.app.models.alert import AlertPolicy, AlertInstance, AlertTemplate
from backend.app.models.notification import NotificationChannel, NotificationTarget
from backend.app.models.client import Client
from backend.app.models.node import Node
from backend.app.models.user import User
from backend.app.notifications.services import NotificationService
from backend.app.exceptions import AlertOperationError

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
    
    def create_policy(self, data: dict, user_id: str) -> AlertPolicy:
        """创建告警策略"""
        try:
            # 验证模板是否存在
            template_id = data.get('template_id')
            if template_id:
                template = AlertTemplate.query.get(template_id)
                if not template:
                    raise AlertOperationError("指定的通知模板不存在")
            
            policy = AlertPolicy(
                name=data['name'],
                description=data.get('description', ''),
                policy_type=data['policy_type'],
                resource_type=data.get('resource_type'),
                alert_items=data.get('alert_items'),
                trigger_rules=data.get('trigger_rules'),
                event_type=data.get('event_type'),
                event_actions=data.get('event_actions'),
                event_results=data.get('event_results'),
                monitored_resources=data.get('monitored_resources'),
                level=data.get('level', 'warning'),
                notification_targets=data.get('notification_targets'),
                retry_count=data.get('retry_count', 3),
                rate_limit=data.get('rate_limit', 300),
                timeout=data.get('timeout', 30),
                enabled=data.get('enabled', True),
                is_default=data.get('is_default', False),
                template_id=template_id,
                user_id=user_id
            )
            
            db.session.add(policy)
            db.session.commit()
            
            logger.info(f"Alert policy created: {policy.id}")
            return policy
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建告警策略失败: {e}")
            raise AlertOperationError(f"创建告警策略失败: {str(e)}")

    def get_policy(self, policy_id: str, user_id: str) -> AlertPolicy:
        """获取告警策略详情"""
        policy = AlertPolicy.query.filter(
            and_(AlertPolicy.id == policy_id, AlertPolicy.user_id == user_id)
        ).first()
        
        if not policy:
            raise ValueError("告警策略不存在")
        
        return policy
    
    def update_policy(self, policy_id: str, data: dict, user_id: str) -> AlertPolicy:
        """更新告警策略"""
        try:
            policy = self.get_policy(policy_id, user_id)
            
            # 验证模板是否存在
            template_id = data.get('template_id')
            if template_id:
                template = AlertTemplate.query.get(template_id)
                if not template:
                    raise AlertOperationError("指定的通知模板不存在")
            
            # 更新字段
            for key, value in data.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
            
            db.session.commit()
            
            logger.info(f"Alert policy updated: {policy_id}")
            return policy
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新告警策略失败: {e}")
            raise AlertOperationError(f"更新告警策略失败: {str(e)}")
    
    def delete_policy(self, policy_id: str, user_id: str) -> None:
        """删除告警策略"""
        try:
            policy = self.get_policy(policy_id, user_id)
            
            # 先删除关联的告警实例
            AlertInstance.query.filter_by(policy_id=policy_id).delete()
            
            # 删除策略
            db.session.delete(policy)
            db.session.commit()
            
            logger.info(f"Alert policy deleted: {policy_id}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除告警策略失败: {e}")
            raise AlertOperationError(f"删除告警策略失败: {str(e)}")
    
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
    
    def get_templates(self, user_id: str = None, category: str = '', template_type: str = '') -> List[Dict[str, Any]]:
        """获取告警策略模板"""
        try:
            # 构建查询
            query = AlertTemplate.query
            
            # 过滤条件
            if category:
                query = query.filter(AlertTemplate.category == category)
            if template_type:
                query = query.filter(AlertTemplate.template_type == template_type)
            
            # 获取系统模板和用户自定义模板
            if user_id:
                query = query.filter(
                    db.or_(
                        AlertTemplate.is_system == True,
                        AlertTemplate.user_id == user_id
                    )
                )
            else:
                query = query.filter(AlertTemplate.is_system == True)
            
            # 按分类和名称排序
            templates = query.order_by(AlertTemplate.category, AlertTemplate.name).all()
            
            return [template.to_dict() for template in templates]
            
        except Exception as e:
            logger.error(f"获取告警模板失败: {e}")
            return []
    
    def create_template(self, data: Dict[str, Any]) -> AlertTemplate:
        """创建告警模板"""
        try:
            self._validate_template_data(data)
            
            template = AlertTemplate(**data)
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"告警模板创建成功: {template.id}")
            return template
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建告警模板失败: {e}")
            raise AlertOperationError(f"创建告警模板失败: {str(e)}")
    
    def get_template(self, template_id: str, user_id: str = None) -> AlertTemplate:
        """获取告警模板详情"""
        try:
            query = AlertTemplate.query.filter_by(id=template_id)
            
            if user_id:
                query = query.filter(
                    db.or_(
                        AlertTemplate.is_system == True,
                        AlertTemplate.user_id == user_id
                    )
                )
            
            template = query.first()
            if not template:
                raise AlertOperationError("告警模板不存在")
            
            return template
            
        except Exception as e:
            logger.error(f"获取告警模板失败: {e}")
            raise AlertOperationError(f"获取告警模板失败: {str(e)}")
    
    def update_template(self, template_id: str, user_id: str, data: Dict[str, Any]) -> AlertTemplate:
        """更新告警模板"""
        try:
            template = self.get_template(template_id, user_id)
            
            # 系统模板只能由管理员修改
            if template.is_system and not self._is_admin(user_id):
                raise AlertOperationError("系统模板只能由管理员修改")
            
            # 更新字段
            for key, value in data.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"告警模板更新成功: {template_id}")
            return template
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新告警模板失败: {e}")
            raise AlertOperationError(f"更新告警模板失败: {str(e)}")
    
    def delete_template(self, template_id: str, user_id: str) -> None:
        """删除告警模板"""
        try:
            template = self.get_template(template_id, user_id)
            
            # 系统模板不能删除
            if template.is_system:
                raise AlertOperationError("系统模板不能删除")
            
            # 检查是否有策略在使用此模板
            policies_count = AlertPolicy.query.filter_by(template_id=template_id).count()
            if policies_count > 0:
                raise AlertOperationError(f"该模板正在被 {policies_count} 个策略使用，无法删除")
            
            db.session.delete(template)
            db.session.commit()
            
            logger.info(f"告警模板删除成功: {template_id}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除告警模板失败: {e}")
            raise AlertOperationError(f"删除告警模板失败: {str(e)}")
    
    def use_template(self, template_id: str, user_id: str) -> Dict[str, Any]:
        """使用模板创建策略"""
        try:
            template = self.get_template(template_id, user_id)
            
            # 更新使用统计
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
            db.session.commit()
            
            # 返回模板配置
            return {
                'template': template.to_dict(),
                'policy_data': self._convert_template_to_policy(template, user_id)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"使用模板失败: {e}")
            raise AlertOperationError(f"使用模板失败: {str(e)}")
    
    def get_template_categories(self) -> List[Dict[str, Any]]:
        """获取模板分类列表"""
        try:
            categories = db.session.query(AlertTemplate.category).distinct().all()
            return [{'id': cat[0], 'name': cat[0]} for cat in categories]
        except Exception as e:
            logger.error(f"获取模板分类失败: {e}")
            return []
    
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
    
    def _send_notifications(self, policy: AlertPolicy, alert_instance: AlertInstance):
        """发送告警通知"""
        try:
            # 渲染通知内容
            notification_content = self.render_policy_notification(policy.id, alert_instance)
            
            if not notification_content:
                logger.warning(f"无法渲染策略 {policy.id} 的通知内容")
                return
            
            # 获取通知目标
            notification_targets = policy.notification_targets or []
            
            for target_config in notification_targets:
                try:
                    target_type = target_config.get('type')
                    target_data = target_config.get('data', {})
                    
                    if target_type == 'email':
                        self._send_email_notification(target_data, notification_content)
                    elif target_type == 'sms':
                        self._send_sms_notification(target_data, notification_content)
                    elif target_type == 'dingtalk':
                        self._send_dingtalk_notification(target_data, notification_content)
                    elif target_type == 'wechat':
                        self._send_wechat_notification(target_data, notification_content)
                    elif target_type == 'webhook':
                        self._send_webhook_notification(target_data, notification_content)
                    else:
                        logger.warning(f"不支持的通知类型: {target_type}")
                        
                except Exception as e:
                    logger.error(f"发送通知失败: {e}")
                    
        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")

    def _send_email_notification(self, target_data: dict, content: dict):
        """发送邮件通知"""
        try:
            # 这里实现邮件发送逻辑
            # 可以使用SMTP或其他邮件服务
            logger.info(f"发送邮件通知: {content['title']}")
            # TODO: 实现实际的邮件发送
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")

    def _send_sms_notification(self, target_data: dict, content: dict):
        """发送短信通知"""
        try:
            # 这里实现短信发送逻辑
            logger.info(f"发送短信通知: {content['content']}")
            # TODO: 实现实际的短信发送
        except Exception as e:
            logger.error(f"发送短信通知失败: {e}")

    def _send_dingtalk_notification(self, target_data: dict, content: dict):
        """发送钉钉通知"""
        try:
            # 这里实现钉钉通知逻辑
            logger.info(f"发送钉钉通知: {content['title']}")
            # TODO: 实现实际的钉钉通知
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")

    def _send_wechat_notification(self, target_data: dict, content: dict):
        """发送企业微信通知"""
        try:
            # 这里实现企业微信通知逻辑
            logger.info(f"发送企业微信通知: {content['title']}")
            # TODO: 实现实际的企业微信通知
        except Exception as e:
            logger.error(f"发送企业微信通知失败: {e}")

    def _send_webhook_notification(self, target_data: dict, content: dict):
        """发送Webhook通知"""
        try:
            # 这里实现Webhook通知逻辑
            logger.info(f"发送Webhook通知: {content['title']}")
            # TODO: 实现实际的Webhook通知
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
    
    def _validate_template_data(self, data: Dict[str, Any]) -> None:
        """验证模板数据"""
        # 必填字段校验
        required_fields = ['name', 'template_type', 'category', 'title_template', 'content_template', 'variables']
        for field in required_fields:
            if field not in data or data[field] in (None, '', []):
                raise AlertOperationError(f"缺少必填字段: {field}")

        # 类型校验
        if not isinstance(data['variables'], list):
            raise AlertOperationError("variables 字段必须为列表类型")
        if 'variable_descriptions' in data and not isinstance(data['variable_descriptions'], dict):
            raise AlertOperationError("variable_descriptions 字段必须为字典类型")

        # 模板类型和分类校验
        valid_template_types = ['email', 'sms', 'dingtalk', 'wechat', 'webhook']
        valid_categories = ['email', 'sms', 'dingtalk', 'wechat', 'webhook']
        if data['template_type'] not in valid_template_types:
            raise AlertOperationError(f"不支持的模板类型: {data['template_type']}")
        if data['category'] not in valid_categories:
            raise AlertOperationError(f"不支持的模板分类: {data['category']}")

        # 模板内容校验
        if not isinstance(data['title_template'], str) or not data['title_template'].strip():
            raise AlertOperationError("title_template 不能为空")
        if not isinstance(data['content_template'], str) or not data['content_template'].strip():
            raise AlertOperationError("content_template 不能为空")
    
    def _convert_template_to_policy(self, template: AlertTemplate, user_id: str) -> Dict[str, Any]:
        """将模板转换为策略数据"""
        policy_data = {
            'name': f"{template.name} - 策略",
            'description': template.description,
            'policy_type': template.template_type,
            'level': template.level,
            'user_id': user_id,
            'enabled': True
        }
        
        if template.template_type == 'resource':
            policy_data.update({
                'resource_type': template.resource_type,
                'alert_items': template.alert_items,
                'trigger_rules': template.trigger_rules
            })
        else:
            policy_data.update({
                'event_type': template.event_type,
                'event_actions': template.event_actions,
                'event_results': template.event_results
            })
        
        return policy_data
    
    def _is_admin(self, user_id: str) -> bool:
        """检查用户是否为管理员"""
        try:
            user = User.query.get(user_id)
            return user and user.role == 'admin'
        except:
            return False
    
    def _init_system_templates(self):
        """初始化系统通知模板"""
        try:
            # 检查是否已有系统模板
            existing_templates = AlertTemplate.query.filter_by(is_system=True).count()
            if existing_templates > 0:
                return
            
            # 系统默认模板
            system_templates = [
                {
                    'name': '默认邮件模板',
                    'description': '系统默认的邮件通知模板',
                    'category': 'email',
                    'template_type': 'email',
                    'title_template': '[{severity}] {alert_name} - {resource_name}',
                    'content_template': '''告警详情：
告警名称: {alert_name}
告警级别: {severity}
资源名称: {resource_name}
当前值: {current_value}
阈值: {threshold}
触发时间: {triggered_at}
告警描述: {description}

请及时处理此告警。''',
                    'variables': ['alert_name', 'severity', 'resource_name', 'current_value', 'threshold', 'triggered_at', 'description'],
                    'variable_descriptions': {
                        'alert_name': '告警策略名称',
                        'severity': '告警级别',
                        'resource_name': '资源名称',
                        'current_value': '当前监控值',
                        'threshold': '触发阈值',
                        'triggered_at': '触发时间',
                        'description': '告警描述'
                    },
                    'is_system': True,
                    'is_default': True
                },
                {
                    'name': '默认钉钉模板',
                    'description': '系统默认的钉钉通知模板',
                    'category': 'dingtalk',
                    'template_type': 'dingtalk',
                    'title_template': '[{severity}] {alert_name}',
                    'content_template': '''## 告警通知

**告警名称**: {alert_name}
**告警级别**: {severity}
**资源名称**: {resource_name}
**当前值**: {current_value}
**阈值**: {threshold}
**触发时间**: {triggered_at}

{description}''',
                    'variables': ['alert_name', 'severity', 'resource_name', 'current_value', 'threshold', 'triggered_at', 'description'],
                    'variable_descriptions': {
                        'alert_name': '告警策略名称',
                        'severity': '告警级别',
                        'resource_name': '资源名称',
                        'current_value': '当前监控值',
                        'threshold': '触发阈值',
                        'triggered_at': '触发时间',
                        'description': '告警描述'
                    },
                    'is_system': True,
                    'is_default': True
                },
                {
                    'name': '默认短信模板',
                    'description': '系统默认的短信通知模板',
                    'category': 'sms',
                    'template_type': 'sms',
                    'title_template': '',
                    'content_template': '[{severity}] {alert_name}: {resource_name} {current_value}/{threshold}',
                    'variables': ['severity', 'alert_name', 'resource_name', 'current_value', 'threshold'],
                    'variable_descriptions': {
                        'severity': '告警级别',
                        'alert_name': '告警策略名称',
                        'resource_name': '资源名称',
                        'current_value': '当前监控值',
                        'threshold': '触发阈值'
                    },
                    'is_system': True,
                    'is_default': True
                }
            ]
            
            for template_data in system_templates:
                template = AlertTemplate(**template_data)
                db.session.add(template)
            
            db.session.commit()
            logger.info("系统通知模板初始化完成")
            
        except Exception as e:
            logger.error(f"初始化系统通知模板失败: {e}")
            db.session.rollback()

    def render_template(self, template_id: str, variables: dict) -> dict:
        """渲染通知模板"""
        try:
            template = AlertTemplate.query.get(template_id)
            if not template:
                raise AlertOperationError("模板不存在")
            
            # 渲染标题和内容
            title = template.title_template
            content = template.content_template
            
            # 替换变量
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                title = title.replace(placeholder, str(value))
                content = content.replace(placeholder, str(value))
            
            return {
                'title': title,
                'content': content,
                'template_type': template.template_type
            }
            
        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
            raise AlertOperationError(f"渲染模板失败: {str(e)}")

    def get_template_variables(self, template_id: str) -> dict:
        """获取模板支持的变量"""
        try:
            template = AlertTemplate.query.get(template_id)
            if not template:
                raise AlertOperationError("模板不存在")
            
            return {
                'variables': template.variables or [],
                'descriptions': template.variable_descriptions or {}
            }
            
        except Exception as e:
            logger.error(f"获取模板变量失败: {e}")
            raise AlertOperationError(f"获取模板变量失败: {str(e)}")

    def get_policies_with_templates(self, user_id: str = None, policy_type: str = '', enabled: bool = None) -> List[Dict[str, Any]]:
        """获取告警策略列表（包含模板信息）"""
        try:
            query = AlertPolicy.query
            
            if user_id:
                query = query.filter(AlertPolicy.user_id == user_id)
            if policy_type:
                query = query.filter(AlertPolicy.policy_type == policy_type)
            if enabled is not None:
                query = query.filter(AlertPolicy.enabled == enabled)
            
            policies = query.order_by(AlertPolicy.created_at.desc()).all()
            
            result = []
            for policy in policies:
                policy_data = policy.to_dict()
                
                # 添加模板信息
                if policy.template:
                    policy_data['template'] = {
                        'id': policy.template.id,
                        'name': policy.template.name,
                        'template_type': policy.template.template_type,
                        'title_template': policy.template.title_template,
                        'content_template': policy.template.content_template
                    }
                
                result.append(policy_data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取告警策略列表失败: {e}")
            return []

    def render_policy_notification(self, policy_id: str, alert_instance: AlertInstance) -> dict:
        """渲染策略的通知内容"""
        try:
            policy = AlertPolicy.query.get(policy_id)
            if not policy or not policy.template:
                return None
            
            # 准备变量数据
            variables = {
                'alert_name': policy.name,
                'severity': policy.level,
                'resource_name': alert_instance.resource_name or '未知资源',
                'current_value': alert_instance.current_value or '未知',
                'threshold': alert_instance.threshold or '未知',
                'triggered_at': alert_instance.triggered_at.strftime('%Y-%m-%d %H:%M:%S') if alert_instance.triggered_at else '未知',
                'description': policy.description or '无描述'
            }
            
            # 渲染模板
            return self.render_template(policy.template.id, variables)
            
        except Exception as e:
            logger.error(f"渲染策略通知失败: {e}")
            return None