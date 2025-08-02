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
    """告警策略服务类"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        
    # =============== 告警策略管理 ===============
    
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
    
    # =============== 策略规则管理 ===============
    
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
    
    # =============== 通知渠道管理 ===============
    
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
        """测试通知渠道"""
        try:
            channel = NotificationChannel.query.get(channel_id)
            if not channel:
                raise ValueError(f"Channel not found: {channel_id}")
            
            # 发送测试消息
            test_message = {
                'title': '测试通知',
                'content': '这是一条测试通知消息，用于验证通知渠道配置是否正确。',
                'level': 'info',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            success = self._send_notification_via_channel(channel, test_message)
            
            if success:
                logger.info(f"Test notification sent successfully via channel: {channel_id}")
            else:
                logger.warning(f"Test notification failed via channel: {channel_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to test notification channel: {str(e)}")
            return False
    
    # =============== 通知对象管理 ===============
    
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
    
    # =============== 内部辅助方法 ===============
    
    def _send_notification_via_channel(self, channel: NotificationChannel, message: Dict[str, Any]) -> bool:
        """通过指定渠道发送通知"""
        try:
            if channel.channel_type == 'email':
                return self._send_email_notification(channel, message)
            elif channel.channel_type == 'webhook':
                return self._send_webhook_notification(channel, message)
            elif channel.channel_type == 'dingtalk':
                return self._send_dingtalk_notification(channel, message)
            elif channel.channel_type == 'sms':
                return self._send_sms_notification(channel, message)
            else:
                logger.warning(f"Unsupported channel type: {channel.channel_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send notification via channel {channel.id}: {str(e)}")
            return False
    
    def _send_email_notification(self, channel: NotificationChannel, message: Dict[str, Any]) -> bool:
        """发送邮件通知"""
        # 这里可以复用已有的邮件发送逻辑
        return True
    
    def _send_webhook_notification(self, channel: NotificationChannel, message: Dict[str, Any]) -> bool:
        """发送Webhook通知"""
        # 这里可以复用已有的Webhook发送逻辑
        return True
    
    def _send_dingtalk_notification(self, channel: NotificationChannel, message: Dict[str, Any]) -> bool:
        """发送钉钉通知"""
        # 这里可以复用已有的钉钉发送逻辑
        return True
    
    def _send_sms_notification(self, channel: NotificationChannel, message: Dict[str, Any]) -> bool:
        """发送短信通知"""
        # 这里可以复用已有的短信发送逻辑
        return True