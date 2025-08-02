from datetime import datetime
from backend import db
from backend.app.models.base import BaseModel
import enum


class AlertLevel(enum.Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(enum.Enum):
    """告警状态"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class Alert(BaseModel):
    """告警模型"""
    __tablename__ = 'alerts'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=True)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    rule_id = db.Column(db.String(36), db.ForeignKey('alert_rules.id'), nullable=True)
    alert_type = db.Column(db.String(50), nullable=False)
    metric = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    level = db.Column(db.Enum(AlertLevel), nullable=False, default=AlertLevel.WARNING)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.Enum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    resolved_at = db.Column(db.DateTime, nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 关联
    rule = db.relationship('AlertRule', backref=db.backref('alerts', lazy=True))
    client = db.relationship('Client', backref=db.backref('alerts', lazy=True))
    node = db.relationship('Node', backref=db.backref('alerts', lazy=True))
    user = db.relationship('User', backref=db.backref('alerts', lazy=True))
    
    # 索引
    __table_args__ = (
        db.Index('idx_node_status', 'node_id', 'status'),
        db.Index('idx_user_level', 'user_id', 'level'),
        db.Index('idx_timestamp', 'timestamp'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'client_id': self.client_id,
            'node_id': self.node_id,
            'rule_id': self.rule_id,
            'alert_type': self.alert_type,
            'metric': self.metric,
            'value': self.value,
            'threshold': self.threshold,
            'level': self.level.value if self.level else None,
            'severity': self.severity,
            'message': self.message,
            'status': self.status.value if self.status else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AlertRule(BaseModel):
    """告警规则模型 - monitor模块使用的简单告警规则"""
    __tablename__ = 'alert_rules'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    metric = db.Column(db.String(50), nullable=False)
    operator = db.Column(db.String(20), nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    # 添加关联
    user = db.relationship('User', backref=db.backref('alert_rules', lazy=True))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'description': self.description,
            'metric': self.metric,
            'operator': self.operator,
            'threshold': self.threshold,
            'duration': self.duration,
            'severity': self.severity,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ========================= 新的告警策略模型 =========================
# 用于alerts模块的策略化告警管理

class AlertPolicy(BaseModel):
    """告警策略模型"""
    __tablename__ = 'alert_policies'
    
    name = db.Column(db.String(100), nullable=False, comment='策略名称')
    description = db.Column(db.Text, comment='策略描述')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 策略类型和分类
    category = db.Column(db.String(50), nullable=False, comment='策略分类: system, task, storage, node, client')
    severity = db.Column(db.String(20), default='warning', comment='告警级别: info, warning, error, critical')
    
    # 触发条件
    conditions = db.Column(db.JSON, comment='触发条件配置')
    
    # 执行配置
    repeat_interval = db.Column(db.Integer, default=3600, comment='重复通知间隔(秒)')
    max_alerts = db.Column(db.Integer, default=10, comment='最大告警次数')
    cooldown_period = db.Column(db.Integer, default=300, comment='冷却期(秒)')
    
    # 恢复条件
    auto_resolve = db.Column(db.Boolean, default=True, comment='是否自动恢复')
    resolve_threshold = db.Column(db.Float, comment='恢复阈值')
    resolve_duration = db.Column(db.Integer, default=300, comment='恢复持续时间(秒)')
    
    # 创建者和权限
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, comment='创建用户')
    is_system = db.Column(db.Boolean, default=False, comment='是否为系统策略')
    
    # 关联关系
    user = db.relationship('User', backref='alert_policies')
    alert_rules = db.relationship('AlertPolicyRule', backref='policy', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'category': self.category,
            'severity': self.severity,
            'conditions': self.conditions,
            'repeat_interval': self.repeat_interval,
            'max_alerts': self.max_alerts,
            'cooldown_period': self.cooldown_period,
            'auto_resolve': self.auto_resolve,
            'resolve_threshold': self.resolve_threshold,
            'resolve_duration': self.resolve_duration,
            'user_id': self.user_id,
            'is_system': self.is_system,
            'username': self.user.username if self.user else None,
            'rules_count': len(self.alert_rules) if self.alert_rules else 0
        })
        return data


class AlertPolicyRule(BaseModel):
    """告警策略规则模型"""
    __tablename__ = 'alert_policy_rules'
    
    policy_id = db.Column(db.String(36), db.ForeignKey('alert_policies.id'), nullable=False)
    
    # 规则配置
    name = db.Column(db.String(100), nullable=False, comment='规则名称')
    metric_name = db.Column(db.String(100), nullable=False, comment='监控指标名称')
    operator = db.Column(db.String(10), nullable=False, comment='比较操作符: >, >=, <, <=, ==, !=')
    threshold_value = db.Column(db.Float, nullable=False, comment='阈值')
    duration = db.Column(db.Integer, default=300, comment='持续时间(秒)')
    
    # 聚合配置
    aggregation_method = db.Column(db.String(20), default='avg', comment='聚合方式: avg, max, min, sum, count')
    evaluation_interval = db.Column(db.Integer, default=60, comment='评估间隔(秒)')
    
    # 标签过滤
    label_filters = db.Column(db.JSON, comment='标签过滤条件')
    
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'policy_id': self.policy_id,
            'name': self.name,
            'metric_name': self.metric_name,
            'operator': self.operator,
            'threshold_value': self.threshold_value,
            'duration': self.duration,
            'aggregation_method': self.aggregation_method,
            'evaluation_interval': self.evaluation_interval,
            'label_filters': self.label_filters,
            'enabled': self.enabled
        })
        return data


class NotificationChannel(BaseModel):
    """通知渠道模型"""
    __tablename__ = 'notification_channels'
    
    name = db.Column(db.String(100), nullable=False, comment='渠道名称')
    description = db.Column(db.Text, comment='渠道描述')
    channel_type = db.Column(db.String(50), nullable=False, comment='渠道类型: email, webhook, dingtalk, sms, slack')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 渠道配置
    config = db.Column(db.JSON, nullable=False, comment='渠道配置')
    
    # 发送限制
    rate_limit = db.Column(db.Integer, default=100, comment='速率限制(次/小时)')
    retry_attempts = db.Column(db.Integer, default=3, comment='重试次数')
    timeout = db.Column(db.Integer, default=30, comment='超时时间(秒)')
    
    # 创建者
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认渠道')
    
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
            'description': self.description,
            'channel_type': self.channel_type,
            'enabled': self.enabled,
            'config': safe_config,
            'rate_limit': self.rate_limit,
            'retry_attempts': self.retry_attempts,
            'timeout': self.timeout,
            'user_id': self.user_id,
            'is_default': self.is_default,
            'username': self.user.username if self.user else None
        })
        return data


class NotificationTarget(BaseModel):
    """通知对象模型"""
    __tablename__ = 'notification_targets'
    
    name = db.Column(db.String(100), nullable=False, comment='对象名称')
    description = db.Column(db.Text, comment='对象描述')
    target_type = db.Column(db.String(50), nullable=False, comment='对象类型: user, group, role, external')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 目标配置
    target_config = db.Column(db.JSON, nullable=False, comment='目标配置')
    
    # 通知时间配置
    notification_schedule = db.Column(db.JSON, comment='通知时间计划')
    
    # 创建者
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # 关联关系
    user = db.relationship('User', backref='notification_targets')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'target_type': self.target_type,
            'enabled': self.enabled,
            'target_config': self.target_config,
            'notification_schedule': self.notification_schedule,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None
        })
        return data


class AlertPolicyAssignment(BaseModel):
    """告警策略分配模型 - 关联策略、渠道和目标"""
    __tablename__ = 'alert_policy_assignments'
    
    policy_id = db.Column(db.String(36), db.ForeignKey('alert_policies.id'), nullable=False)
    channel_id = db.Column(db.String(36), db.ForeignKey('notification_channels.id'), nullable=False)
    target_id = db.Column(db.String(36), db.ForeignKey('notification_targets.id'), nullable=False)
    
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    priority = db.Column(db.Integer, default=0, comment='优先级，数字越大优先级越高')
    
    # 过滤条件
    filters = db.Column(db.JSON, comment='附加过滤条件')
    
    # 关联关系
    policy = db.relationship('AlertPolicy', backref='assignments')
    channel = db.relationship('NotificationChannel', backref='assignments')
    target = db.relationship('NotificationTarget', backref='assignments')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'policy_id': self.policy_id,
            'channel_id': self.channel_id,
            'target_id': self.target_id,
            'enabled': self.enabled,
            'priority': self.priority,
            'filters': self.filters,
            'policy_name': self.policy.name if self.policy else None,
            'channel_name': self.channel.name if self.channel else None,
            'target_name': self.target.name if self.target else None
        })
        return data


class AlertInstance(BaseModel):
    """告警实例模型 - 具体的告警事件"""
    __tablename__ = 'alert_instances'
    
    policy_id = db.Column(db.String(36), db.ForeignKey('alert_policies.id'), nullable=False)
    rule_id = db.Column(db.String(36), db.ForeignKey('alert_policy_rules.id'), nullable=False)
    
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
    rule = db.relationship('AlertPolicyRule', backref='instances')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'policy_id': self.policy_id,
            'rule_id': self.rule_id,
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
            'policy_name': self.policy.name if self.policy else None,
            'rule_name': self.rule.name if self.rule else None
        })
        return data


 