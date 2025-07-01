from backend import db
from backend.app.models.base import BaseModel

class BandwidthPolicy(BaseModel):
    """带宽策略模型"""
    __tablename__ = 'bandwidth_policies'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    max_bandwidth = db.Column(db.Integer, nullable=False)
    schedule = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关联
    task = db.relationship('Task', backref=db.backref('bandwidth_policies', lazy=True))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('bandwidth_policies', lazy=True))
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'task_id': self.task_id,
            'name': self.name,
            'max_bandwidth': self.max_bandwidth,
            'schedule': self.schedule,
            'is_active': self.is_active
        })
        return data

class BackupPolicy(BaseModel):
    """备份策略模型"""
    __tablename__ = 'backup_policies'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    backup_type = db.Column(db.String(20), nullable=False)
    retention_days = db.Column(db.Integer, nullable=False)
    schedule = db.Column(db.JSON)
    storage_id = db.Column(db.String(36), db.ForeignKey('storages.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关联
    task = db.relationship('Task', backref=db.backref('backup_policies', lazy=True))
    storage = db.relationship('Storage', backref=db.backref('backup_policies', lazy=True))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('backup_policies', lazy=True))
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'task_id': self.task_id,
            'name': self.name,
            'backup_type': self.backup_type,
            'retention_days': self.retention_days,
            'schedule': self.schedule,
            'storage_id': self.storage_id,
            'is_active': self.is_active
        })
        return data

class EncryptionKey(BaseModel):
    """加密密钥模型"""
    __tablename__ = 'encryption_keys'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    key_name = db.Column(db.String(100), nullable=False)
    key_type = db.Column(db.String(20), nullable=False)
    key_data = db.Column(db.Text, nullable=False)
    iv = db.Column(db.String(32))
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # 关联
    task = db.relationship('Task', backref='encryption_keys', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_keys', lazy=True)
    user = db.relationship('User', foreign_keys=[user_id], backref='encryption_keys', lazy=True)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'task_id': self.task_id,
            'key_name': self.key_name,
            'key_type': self.key_type,
            'created_by': self.created_by
        })
        return data 