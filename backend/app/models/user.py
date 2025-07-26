from werkzeug.security import generate_password_hash, check_password_hash
from backend.app.models.base import BaseModel
from backend import db

class User(BaseModel):
    """用户模型"""
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')  # 用户角色：user, admin
    is_active = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(255))  # 头像
    last_login = db.Column(db.DateTime)  # 最后登录时间
    last_login_ip = db.Column(db.String(45))  # 最后登录IP
    login_count = db.Column(db.Integer, default=0)  # 登录次数
    last_login_location = db.Column(db.String(100))  # 最后登录位置
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(128), nullable=True)
    reset_password_token = db.Column(db.String(128), nullable=True)
    reset_password_expire = db.Column(db.DateTime, nullable=True)

    # 关系
    storages = db.relationship('Storage', backref='owner', lazy='dynamic')
    tasks = db.relationship('Task', backref='owner', lazy='dynamic')
    notifications = db.relationship('Notification', backref='owner', lazy='dynamic')
    clients = db.relationship('Client', backref='owner', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def __init__(self, username, email, password=None, role='user'):
        self.username = username
        self.email = email
        self.role = role
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'avatar': self.avatar,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_login_ip': self.last_login_ip,
            'login_count': self.login_count,
            'last_login_location': self.last_login_location
        })
        return data
    
    def __repr__(self):
        return f'<User {self.username}>' 

class AuditLog(BaseModel):
    """审计日志模型"""
    __tablename__ = 'audit_logs'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(32), nullable=False)
    resource_type = db.Column(db.String(32), nullable=False)
    resource_id = db.Column(db.String(36))
    resource_name = db.Column(db.String(255))  # 资源名称
    details = db.Column(db.JSON)
    result = db.Column(db.String(20), default='success')  # success, failed
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'details': self.details,
            'result': self.result
        })
        return data

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
    # 关联
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notification_setting', lazy=True))

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'enabled': self.enabled,
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
            'sms_sign_name': self.sms_sign_name
        })
        return data