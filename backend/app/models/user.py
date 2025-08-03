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