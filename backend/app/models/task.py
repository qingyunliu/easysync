from datetime import datetime
from enum import Enum
from backend.app.models.base import BaseModel
from backend import db

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class Task(BaseModel):
    """同步任务模型"""
    __tablename__ = 'tasks'
    
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default=TaskStatus.PENDING.value)
    priority = db.Column(db.Integer, default=TaskPriority.NORMAL.value)
    source = db.Column(db.JSON, nullable=False)
    target = db.Column(db.JSON, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    assigned_node = db.Column(db.String(36), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.String(500), nullable=True)
    progress = db.Column(db.Integer, default=0)
    details = db.Column(db.JSON, nullable=True)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=False)

    # 关联
    logs = db.relationship('TaskLog', backref=db.backref('task', lazy=True))
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            'priority': self.priority,
            'source': self.source,
            'target': self.target,
            'options': self.options,
            'assigned_node': self.assigned_node,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'progress': self.progress,
            'details': self.details,
        })
        return data


class TaskLog(BaseModel):
    __tablename__ = "task_logs"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey("tasks.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    details = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "id": self.id,
            "task_id": self.task_id,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat()
        })
        return data