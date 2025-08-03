from datetime import datetime
from backend import db
from backend.app.models.base import BaseModel


class AlertPolicy(BaseModel):
    """告警策略模型"""
    __tablename__ = 'alert_policies'
    
    name = db.Column(db.String(100), nullable=False, comment='告警器名称')
    description = db.Column(db.Text, comment='告警器描述')
    level = db.Column(db.String(20), default='warning', comment='告警级别: info, warning, error, critical')
    enabled = db.Column(db.Boolean, default=True, comment='启动状态')
    
    # 策略类型
    policy_type = db.Column(db.String(20), nullable=False, comment='策略类型: resource, event')
    
    # 资源告警配置
    resource_type = db.Column(db.String(50), comment='资源类型: Nodes, Clients, 系统')
    monitored_resources = db.Column(db.JSON, comment='监控资源列表')
    alert_items = db.Column(db.JSON, comment='报警条目: CPU、内存、磁盘等')
    trigger_rules = db.Column(db.JSON, comment='触发规则配置')
    
    # 事件告警配置
    event_type = db.Column(db.String(50), comment='事件类型: 存储、客户端、代理等')
    event_actions = db.Column(db.JSON, comment='事件动作: 创建、删除、获取等')
    event_results = db.Column(db.JSON, comment='事件结果: success, failed, timeout等')
    
    # 通知配置
    notification_targets = db.Column(db.JSON, comment='关联的通知对象ID列表')
    
    # 创建者
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, comment='创建用户')
    
    # 关联关系
    user = db.relationship('User', backref='alert_policies')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'enabled': self.enabled,
            'policy_type': self.policy_type,
            'resource_type': self.resource_type,
            'monitored_resources': self.monitored_resources,
            'alert_items': self.alert_items,
            'trigger_rules': self.trigger_rules,
            'event_type': self.event_type,
            'event_actions': self.event_actions,
            'event_results': self.event_results,
            'notification_targets': self.notification_targets,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None
        })
        return data


class NotificationChannel(BaseModel):
    """通知渠道模型"""
    __tablename__ = 'notification_channels'
    
    name = db.Column(db.String(100), nullable=False, comment='渠道名称')
    channel_type = db.Column(db.String(50), nullable=False, comment='渠道类型: email, sms, webhook, dingtalk, slack')
    enabled = db.Column(db.Boolean, default=True, comment='启动状态')
    
    # 渠道配置
    config = db.Column(db.JSON, nullable=False, comment='渠道配置')
    
    # 发送限制
    retry_count = db.Column(db.Integer, default=3, comment='重试发送次数')
    rate_limit = db.Column(db.Integer, default=100, comment='速率限制(次/小时)')
    timeout = db.Column(db.Integer, default=30, comment='超时时间(秒)')
    
    # 默认设置
    is_default = db.Column(db.Boolean, default=False, comment='是否设置为默认')
    
    # 创建者
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # 关联关系
    user = db.relationship('User', backref='notification_channels')
    
    def to_dict(self):
        data = super().to_dict()
        # 隐藏敏感配置信息
        safe_config = self.config.copy() if self.config else {}
        if 'password' in safe_config:
            safe_config['password'] = '******'
        if 'secret' in safe_config:
            safe_config['secret'] = '******'
        if 'api_key' in safe_config:
            safe_config['api_key'] = '******'
            
        data.update({
            'name': self.name,
            'channel_type': self.channel_type,
            'enabled': self.enabled,
            'config': safe_config,
            'retry_count': self.retry_count,
            'rate_limit': self.rate_limit,
            'timeout': self.timeout,
            'is_default': self.is_default,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None
        })
        return data


class NotificationTarget(BaseModel):
    """通知对象模型"""
    __tablename__ = 'notification_targets'
    
    name = db.Column(db.String(100), nullable=False, comment='通知对象名称')
    enabled = db.Column(db.Boolean, default=True, comment='启动状态')
    description = db.Column(db.Text, comment='描述')
    
    # 关联的告警器
    alert_policies = db.Column(db.JSON, comment='关联的告警器ID列表')
    
    # 发送通道
    channels = db.Column(db.JSON, comment='关联的通知渠道ID列表')
    
    # 通知对象配置
    target_type = db.Column(db.String(50), nullable=False, comment='通知对象类型: email, sms, webhook等')
    target_config = db.Column(db.JSON, nullable=False, comment='通知对象配置')
    
    # 创建者
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # 关联关系
    user = db.relationship('User', backref='notification_targets')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'enabled': self.enabled,
            'description': self.description,
            'alert_policies': self.alert_policies,
            'channels': self.channels,
            'target_type': self.target_type,
            'target_config': self.target_config,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None
        })
        return data


class AlertInstance(BaseModel):
    """告警实例模型 - 具体的告警事件"""
    __tablename__ = 'alert_instances'
    
    policy_id = db.Column(db.String(36), db.ForeignKey('alert_policies.id'), nullable=False)
    
    # 告警信息
    alert_name = db.Column(db.String(200), nullable=False, comment='告警名称')
    severity = db.Column(db.String(20), nullable=False, comment='告警级别')
    status = db.Column(db.String(20), default='firing', comment='告警状态: firing, resolved, suppressed')
    
    # 指标信息
    metric_name = db.Column(db.String(100), nullable=False, comment='指标名称')
    current_value = db.Column(db.Float, comment='当前值')
    threshold_value = db.Column(db.Float, comment='阈值')
    
    # 标签和上下文
    labels = db.Column(db.JSON, comment='告警标签')
    annotations = db.Column(db.JSON, comment='告警注释')
    fingerprint = db.Column(db.String(64), nullable=False, index=True, comment='告警指纹')
    
    # 时间信息
    starts_at = db.Column(db.DateTime, nullable=False, comment='告警开始时间')
    ends_at = db.Column(db.DateTime, comment='告警结束时间')
    resolved_at = db.Column(db.DateTime, comment='告警解决时间')
    
    # 统计信息
    notification_count = db.Column(db.Integer, default=0, comment='通知次数')
    last_notification_at = db.Column(db.DateTime, comment='最后通知时间')
    
    # 关联关系
    policy = db.relationship('AlertPolicy', backref='instances')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'policy_id': self.policy_id,
            'alert_name': self.alert_name,
            'severity': self.severity,
            'status': self.status,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'labels': self.labels,
            'annotations': self.annotations,
            'fingerprint': self.fingerprint,
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'ends_at': self.ends_at.isoformat() if self.ends_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'notification_count': self.notification_count,
            'last_notification_at': self.last_notification_at.isoformat() if self.last_notification_at else None,
            'policy_name': self.policy.name if self.policy else None
        })
        return data