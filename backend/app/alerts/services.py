import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend import db
from backend.app.models import (
    AlertPolicy, AlertPolicyRule, NotificationChannel, 
    NotificationTarget, AlertPolicyAssignment, AlertInstance,
    User, NotificationSetting
)
from backend.app.notifications.services import NotificationService

logger = logging.getLogger(__name__)

class AlertPolicyService:
    """告警策略服务类 - 专注于告警策略管理"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def create_policy(self, user_id: str, policy_data: Dict[str, Any]) -> AlertPolicy:
        """创建告警策略"""
        try:
            policy = AlertPolicy(
                name=policy_data['name'],
                description=policy_data.get('description'),
                category=policy_data['category'],
                severity=policy_data.get('severity', 'warning'),
                conditions=policy_data.get('conditions', {}),
                repeat_interval=policy_data.get('repeat_interval', 3600),
                max_alerts=policy_data.get('max_alerts', 10),
                cooldown_period=policy_data.get('cooldown_period', 300),
                auto_resolve=policy_data.get('auto_resolve', True),
                resolve_threshold=policy_data.get('resolve_threshold'),
                resolve_duration=policy_data.get('resolve_duration', 300),
                user_id=user_id,
                enabled=policy_data.get('enabled', True)
            )
            
            db.session.add(policy)
            db.session.commit()
            
            # 创建规则
            if 'rules' in policy_data:
                for rule_data in policy_data['rules']:
                    self.create_policy_rule(policy.id, rule_data)
            
            logger.info(f"Alert policy created: {policy.id}")
            return policy
            
        except Exception as e:
            logger.error(f"Failed to create alert policy: {str(e)}")
            db.session.rollback()
            raise
    
    def get_policy(self, policy_id: str) -> Optional[AlertPolicy]:
        """获取告警策略"""
        return AlertPolicy.query.get(policy_id)
    
    def get_policies(self, user_id: str = None, category: str = None, 
                    enabled: bool = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """获取告警策略列表"""
        query = AlertPolicy.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if category:
            query = query.filter_by(category=category)
            
        if enabled is not None:
            query = query.filter_by(enabled=enabled)
        
        # 分页
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'policies': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    
    def update_policy(self, policy_id: str, policy_data: Dict[str, Any]) -> AlertPolicy:
        """更新告警策略"""
        try:
            policy = self.get_policy(policy_id)
            if not policy:
                raise ValueError(f"Policy not found: {policy_id}")
            
            # 更新基本信息
            for field in ['name', 'description', 'category', 'severity', 'conditions',
                         'repeat_interval', 'max_alerts', 'cooldown_period', 'auto_resolve',
                         'resolve_threshold', 'resolve_duration', 'enabled']:
                if field in policy_data:
                    setattr(policy, field, policy_data[field])
            
            policy.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Alert policy updated: {policy_id}")
            return policy
            
        except Exception as e:
            logger.error(f"Failed to update alert policy: {str(e)}")
            db.session.rollback()
            raise
    
    def delete_policy(self, policy_id: str) -> bool:
        """删除告警策略"""
        try:
            policy = self.get_policy(policy_id)
            if not policy:
                raise ValueError(f"Policy not found: {policy_id}")
            
            db.session.delete(policy)
            db.session.commit()
            
            logger.info(f"Alert policy deleted: {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete alert policy: {str(e)}")
            db.session.rollback()
            raise
    
    def create_policy_rule(self, policy_id: str, rule_data: Dict[str, Any]) -> AlertPolicyRule:
        """创建策略规则"""
        try:
            rule = AlertPolicyRule(
                policy_id=policy_id,
                name=rule_data['name'],
                metric_name=rule_data['metric_name'],
                operator=rule_data['operator'],
                threshold_value=rule_data['threshold_value'],
                duration=rule_data.get('duration', 300),
                aggregation_method=rule_data.get('aggregation_method', 'avg'),
                evaluation_interval=rule_data.get('evaluation_interval', 60),
                label_filters=rule_data.get('label_filters', {}),
                enabled=rule_data.get('enabled', True)
            )
            
            db.session.add(rule)
            db.session.commit()
            
            logger.info(f"Alert policy rule created: {rule.id}")
            return rule
            
        except Exception as e:
            logger.error(f"Failed to create alert policy rule: {str(e)}")
            db.session.rollback()
            raise
    
    def get_policy_rules(self, policy_id: str) -> List[AlertPolicyRule]:
        """获取策略规则列表"""
        return AlertPolicyRule.query.filter_by(policy_id=policy_id).all()
    
    def create_notification_channel(self, user_id: str, channel_data: Dict[str, Any]) -> NotificationChannel:
        """创建通知渠道"""
        try:
            channel = NotificationChannel(
                name=channel_data['name'],
                description=channel_data.get('description'),
                channel_type=channel_data['channel_type'],
                config=channel_data['config'],
                rate_limit=channel_data.get('rate_limit', 100),
                retry_attempts=channel_data.get('retry_attempts', 3),
                timeout=channel_data.get('timeout', 30),
                user_id=user_id,
                enabled=channel_data.get('enabled', True)
            )
            
            db.session.add(channel)
            db.session.commit()
            
            logger.info(f"Notification channel created: {channel.id}")
            return channel
            
        except Exception as e:
            logger.error(f"Failed to create notification channel: {str(e)}")
            db.session.rollback()
            raise
    
    def get_notification_channels(self, user_id: str = None, channel_type: str = None) -> List[NotificationChannel]:
        """获取通知渠道列表"""
        query = NotificationChannel.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if channel_type:
            query = query.filter_by(channel_type=channel_type)
        
        return query.all()
    
    def test_notification_channel(self, channel_id: str) -> bool:
        """测试通知渠道 - 使用notifications服务发送测试消息"""
        try:
            channel = NotificationChannel.query.get(channel_id)
            if not channel:
                raise ValueError(f"Channel not found: {channel_id}")
            
            # 使用notifications服务发送测试消息
            test_message = {
                'title': '告警渠道测试',
                'content': '这是一条测试告警消息，用于验证告警渠道配置是否正确。',
                'level': 'info',
                'type': 'alert_test',
                'metadata': {
                    'channel_id': channel_id,
                    'channel_type': channel.channel_type,
                    'test': True
                }
            }
            
            # 通过notifications服务发送
            self.notification_service.send_notification(
                level='info',
                title=test_message['title'],
                content=test_message['content'],
                user_id=channel.user_id,
                metadata=test_message['metadata']
            )
            
            logger.info(f"Test notification sent successfully via channel: {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to test notification channel: {str(e)}")
            return False
    
    def create_notification_target(self, user_id: str, target_data: Dict[str, Any]) -> NotificationTarget:
        """创建通知对象"""
        try:
            target = NotificationTarget(
                name=target_data['name'],
                description=target_data.get('description'),
                target_type=target_data['target_type'],
                target_config=target_data['target_config'],
                notification_schedule=target_data.get('notification_schedule', {}),
                user_id=user_id,
                enabled=target_data.get('enabled', True)
            )
            
            db.session.add(target)
            db.session.commit()
            
            logger.info(f"Notification target created: {target.id}")
            return target
            
        except Exception as e:
            logger.error(f"Failed to create notification target: {str(e)}")
            db.session.rollback()
            raise
    
    def get_notification_targets(self, user_id: str = None, target_type: str = None) -> List[NotificationTarget]:
        """获取通知对象列表"""
        query = NotificationTarget.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if target_type:
            query = query.filter_by(target_type=target_type)
        
        return query.all()
    
    def trigger_alert(self, user_id: str, alert_data: Dict[str, Any]) -> bool:
        """触发告警 - 使用notifications服务发送告警通知"""
        try:
            # 创建告警实例
            alert_instance = AlertInstance(
                policy_id=alert_data.get('policy_id'),
                rule_id=alert_data.get('rule_id'),
                alert_name=alert_data['alert_type'],
                severity=alert_data.get('severity', 'warning'),
                metric_name=alert_data.get('metric_name', 'unknown'),
                current_value=alert_data.get('current_value'),
                threshold_value=alert_data.get('threshold_value'),
                labels=alert_data.get('labels', {}),
                annotations={'message': alert_data['message']},
                fingerprint=alert_data.get('fingerprint', ''),
                starts_at=datetime.utcnow(),
                **alert_data.get('metadata', {})
            )
            
            db.session.add(alert_instance)
            db.session.commit()
            
            # 通过notifications服务发送告警通知
            self.notification_service.send_notification(
                level=alert_data.get('severity', 'warning'),
                title=f"告警: {alert_data['alert_type']}",
                content=alert_data['message'],
                user_id=user_id,
                metadata={
                    'alert_instance_id': alert_instance.id,
                    'alert_type': alert_data['alert_type'],
                    'policy_id': alert_data.get('policy_id'),
                    **alert_data.get('metadata', {})
                }
            )
            
            logger.info(f"Alert triggered: {alert_instance.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {str(e)}")
            db.session.rollback()
            return False
    
    def resolve_alert(self, alert_instance_id: str, user_id: str = None) -> bool:
        """解决告警"""
        try:
            alert_instance = AlertInstance.query.get(alert_instance_id)
            if not alert_instance:
                raise ValueError(f"Alert instance not found: {alert_instance_id}")
            
            alert_instance.status = 'resolved'
            alert_instance.resolved_at = datetime.utcnow()
            db.session.commit()
            
            # 发送告警解决通知
            self.notification_service.send_notification(
                level='success',
                title=f"告警已解决: {alert_instance.alert_name}",
                content=f"告警 {alert_instance.alert_name} 已被解决。",
                user_id=user_id or alert_instance.policy.user_id,
                metadata={
                    'alert_instance_id': alert_instance_id,
                    'alert_type': alert_instance.alert_name,
                    'resolved': True
                }
            )
            
            logger.info(f"Alert resolved: {alert_instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {str(e)}")
            db.session.rollback()
            return False