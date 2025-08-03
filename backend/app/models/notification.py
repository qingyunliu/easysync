from backend.app.models.base import BaseModel
from backend import db

class Notification(BaseModel):
    """通知模型"""
    __tablename__ = 'notifications'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    level = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'level': self.level,
            'is_read': self.is_read
        })
        return data

class NotificationSetting(BaseModel):
    """通知设置模型"""
    __tablename__ = 'notification_settings'
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    
    # 通知策略类型配置
    notification_policies = db.Column(db.JSON, comment='通知策略配置')
    """
    通知策略配置示例:
    {
        "task_completion": {
            "enabled": true,
            "channels": ["email", "webhook"],
            "severity": ["success", "error"]
        },
        "storage_error": {
            "enabled": true,
            "channels": ["email"],
            "severity": ["error", "warning"]
        },
        "system_alert": {
            "enabled": false,
            "channels": ["webhook"],
            "severity": ["critical", "error"]
        }
    }
    """
    
    # 邮件
    email_enabled = db.Column(db.Boolean, default=False)
    smtp_host = db.Column(db.String(255))
    smtp_port = db.Column(db.Integer)
    smtp_username = db.Column(db.String(255))
    smtp_password = db.Column(db.String(255))  # 可加密
    email = db.Column(db.String(255))
    # webhook
    webhook_enabled = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(500))
    webhook_secret = db.Column(db.String(255))  # 可加密
    # 钉钉
    dingtalk_enabled = db.Column(db.Boolean, default=False)
    dingtalk_webhook = db.Column(db.String(500))
    dingtalk_secret = db.Column(db.String(255))  # 可加密
    # 短信
    sms_enabled = db.Column(db.Boolean, default=False)
    sms_provider = db.Column(db.String(50))
    sms_api_key = db.Column(db.String(255))  # 可加密
    sms_template_id = db.Column(db.String(255))
    sms_sign_name = db.Column(db.String(255))
    
    # 通知偏好设置
    quiet_hours = db.Column(db.JSON, comment='免打扰时间配置')
    """
    免打扰时间配置示例:
    {
        "enabled": true,
        "start_time": "22:00",
        "end_time": "08:00",
        "timezone": "Asia/Shanghai",
        "weekends_only": false
    }
    """
    
    # 关联
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notification_setting', lazy=True))

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'enabled': self.enabled,
            'notification_policies': self.notification_policies or {},
            'email_enabled': self.email_enabled,
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'smtp_password': self.smtp_password,
            'email': self.email,
            'webhook_enabled': self.webhook_enabled,
            'webhook_url': self.webhook_url,
            'webhook_secret': self.webhook_secret,
            'dingtalk_enabled': self.dingtalk_enabled,
            'dingtalk_webhook': self.dingtalk_webhook,
            'dingtalk_secret': self.dingtalk_secret,
            'sms_enabled': self.sms_enabled,
            'sms_provider': self.sms_provider,
            'sms_api_key': self.sms_api_key,
            'sms_template_id': self.sms_template_id,
            'sms_sign_name': self.sms_sign_name,
            'quiet_hours': self.quiet_hours or {}
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