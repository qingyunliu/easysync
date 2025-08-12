from datetime import datetime
from backend import db
from backend.app.models.base import BaseModel


class AlertResourceType(BaseModel):
    """告警资源类型模型 - 存储可监控的资源类型"""
    __tablename__ = 'alert_resource_types'
    
    name = db.Column(db.String(50), nullable=False, comment='资源类型名称')
    code = db.Column(db.String(50), nullable=False, unique=True, comment='资源类型代码')
    description = db.Column(db.Text, comment='资源类型描述')
    category = db.Column(db.String(50), nullable=False, comment='资源分类: system, storage, client, node等')
    icon = db.Column(db.String(100), comment='资源类型图标')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 关联关系
    alert_items = db.relationship('AlertResourceItem', backref='resource_type', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'enabled': self.enabled
        })
        return data


class AlertResourceItem(BaseModel):
    """告警资源条目模型 - 存储具体的监控指标"""
    __tablename__ = 'alert_resource_items'
    
    resource_type_id = db.Column(db.String(36), db.ForeignKey('alert_resource_types.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False, comment='条目名称')
    code = db.Column(db.String(50), nullable=False, comment='条目代码')
    description = db.Column(db.Text, comment='条目描述')
    unit = db.Column(db.String(20), comment='单位: %, MB, GB, ms等')
    data_type = db.Column(db.String(20), default='float', comment='数据类型: float, int, string等')
    default_threshold = db.Column(db.Float, comment='默认阈值')
    min_value = db.Column(db.Float, comment='最小值')
    max_value = db.Column(db.Float, comment='最大值')
    operators = db.Column(db.JSON, comment='支持的比较操作符: >, >=, <, <=, ==, !=')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'resource_type_id': self.resource_type_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'unit': self.unit,
            'data_type': self.data_type,
            'default_threshold': self.default_threshold,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'operators': self.operators,
            'sort_order': self.sort_order,
            'enabled': self.enabled
        })
        return data


class AlertEventType(BaseModel):
    """告警事件类型模型 - 存储可监控的事件类型"""
    __tablename__ = 'alert_event_types'
    
    name = db.Column(db.String(50), nullable=False, comment='事件类型名称')
    code = db.Column(db.String(50), nullable=False, unique=True, comment='事件类型代码')
    description = db.Column(db.Text, comment='事件类型描述')
    category = db.Column(db.String(50), nullable=False, comment='事件分类: user, storage, client, node, sync等')
    icon = db.Column(db.String(100), comment='事件类型图标')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 关联关系
    event_actions = db.relationship('AlertEventAction', backref='event_type', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'enabled': self.enabled
        })
        return data


class AlertEventAction(BaseModel):
    """告警事件动作模型 - 存储具体的事件动作"""
    __tablename__ = 'alert_event_actions'
    
    event_type_id = db.Column(db.String(36), db.ForeignKey('alert_event_types.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False, comment='动作名称')
    code = db.Column(db.String(50), nullable=False, comment='动作代码')
    description = db.Column(db.Text, comment='动作描述')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'event_type_id': self.event_type_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'sort_order': self.sort_order,
            'enabled': self.enabled
        })
        return data


class AlertEventResult(BaseModel):
    """告警事件结果模型 - 存储事件结果类型"""
    __tablename__ = 'alert_event_results'
    
    name = db.Column(db.String(20), nullable=False, comment='结果名称')
    code = db.Column(db.String(20), nullable=False, unique=True, comment='结果代码')
    description = db.Column(db.Text, comment='结果描述')
    color = db.Column(db.String(20), comment='显示颜色')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'color': self.color,
            'sort_order': self.sort_order,
            'enabled': self.enabled
        })
        return data


class AlertPolicy(BaseModel):
    """告警策略模型"""
    __tablename__ = 'alert_policies'
    
    name = db.Column(db.String(100), nullable=False, comment='策略名称')
    description = db.Column(db.Text, comment='策略描述')
    
    # 策略类型
    policy_type = db.Column(db.String(20), nullable=False, comment='策略类型: resource, event')
    
    # 资源策略配置
    resource_type = db.Column(db.String(50), comment='资源类型: Nodes, Clients, 系统')
    alert_items = db.Column(db.JSON, comment='报警条目: CPU、内存、磁盘等')
    trigger_rules = db.Column(db.JSON, comment='触发规则配置')
    
    # 事件策略配置
    event_type = db.Column(db.String(50), comment='事件类型: 存储、客户端、代理等')
    event_actions = db.Column(db.JSON, comment='事件动作: 创建、删除、获取等')
    event_results = db.Column(db.JSON, comment='事件结果: success, failed, timeout等')
    
    # 监控配置
    monitored_resources = db.Column(db.JSON, comment='监控的资源ID列表')
    level = db.Column(db.String(20), default='warning', comment='告警级别: info, warning, error, critical')
    
    # 通知配置
    notification_targets = db.Column(db.JSON, comment='通知目标配置')
    retry_count = db.Column(db.Integer, default=3, comment='重试次数')
    rate_limit = db.Column(db.Integer, default=300, comment='频率限制(秒)')
    timeout = db.Column(db.Integer, default=30, comment='超时时间(秒)')
    
    # 状态配置
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认策略')
    
    # 关联模板
    template_id = db.Column(db.String(36), db.ForeignKey('alert_templates.id'), nullable=True, comment='关联的通知模板ID')
    
    # 创建者
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, comment='创建用户')
    
    # 关联关系
    user = db.relationship('User', backref='alert_policies')
    template = db.relationship('AlertTemplate', backref='policies')
    instances = db.relationship('AlertInstance', backref='policy', cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'policy_type': self.policy_type,
            'resource_type': self.resource_type,
            'alert_items': self.alert_items,
            'trigger_rules': self.trigger_rules,
            'event_type': self.event_type,
            'event_actions': self.event_actions,
            'event_results': self.event_results,
            'monitored_resources': self.monitored_resources,
            'level': self.level,
            'notification_targets': self.notification_targets,
            'retry_count': self.retry_count,
            'rate_limit': self.rate_limit,
            'timeout': self.timeout,
            'enabled': self.enabled,
            'is_default': self.is_default,
            'template_id': self.template_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'template_name': self.template.name if self.template else None
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


class AlertTemplate(BaseModel):
    """告警通知模板模型"""
    __tablename__ = 'alert_templates'
    
    name = db.Column(db.String(100), nullable=False, comment='模板名称')
    description = db.Column(db.Text, comment='模板描述')
    category = db.Column(db.String(50), nullable=False, comment='模板分类: email, sms, dingtalk, wechat等')
    
    # 模板类型
    template_type = db.Column(db.String(20), nullable=False, comment='模板类型: email, sms, webhook, dingtalk, wechat')
    
    # 通知配置
    title_template = db.Column(db.Text, nullable=False, comment='标题模板')
    content_template = db.Column(db.Text, nullable=False, comment='内容模板')
    
    # 变量配置
    variables = db.Column(db.JSON, comment='支持的变量列表')
    variable_descriptions = db.Column(db.JSON, comment='变量说明')
    
    # 模板配置
    is_system = db.Column(db.Boolean, default=False, comment='是否系统模板')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认模板')
    
    # 使用统计
    usage_count = db.Column(db.Integer, default=0, comment='使用次数')
    last_used_at = db.Column(db.DateTime, comment='最后使用时间')
    
    # 创建者
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, comment='创建用户(系统模板为null)')
    
    # 关联关系
    user = db.relationship('User', backref='alert_templates')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'template_type': self.template_type,
            'title_template': self.title_template,
            'content_template': self.content_template,
            'variables': self.variables,
            'variable_descriptions': self.variable_descriptions,
            'is_system': self.is_system,
            'is_default': self.is_default,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None
        })
        return data