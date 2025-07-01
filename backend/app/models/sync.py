from backend.app.models.base import BaseModel
from backend import db

class SyncRule(BaseModel):
    """同步规则模型"""
    __tablename__ = 'sync_rules'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    pattern = db.Column(db.String(200), nullable=False)
    include_pattern = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)
    
    # 关联
    task = db.relationship('Task', backref=db.backref('sync_rules', lazy=True))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('sync_rules', lazy=True))
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'task_id': self.task_id,
            'pattern': self.pattern,
            'include_pattern': self.include_pattern,
            'priority': self.priority
        })
        return data