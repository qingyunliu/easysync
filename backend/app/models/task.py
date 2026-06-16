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
    
    # 新的任务配置字段
    source_type = db.Column(db.String(20), nullable=False)  # client 或 storage
    source_client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=True)  # 源端客户端ID
    source_storage_id = db.Column(db.String(36), db.ForeignKey('storages.id'), nullable=True)  # 源端存储ID
    source_path = db.Column(db.String(500), nullable=False)  # 源端路径
    target_storage_id = db.Column(db.String(36), db.ForeignKey('storages.id'), nullable=False)  # 目标存储ID
    target_path = db.Column(db.String(500), nullable=False)  # 目标路径
    
    # 兼容旧版本的字段
    source = db.Column(db.JSON, nullable=True)
    target = db.Column(db.JSON, nullable=True)
    options = db.Column(db.JSON, nullable=False)
    
    assigned_node = db.Column(db.String(36), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.String(500), nullable=True)
    progress = db.Column(db.Integer, default=0)
    details = db.Column(db.JSON, nullable=True)
    auto_start = db.Column(db.Boolean, default=False)  # 是否自动启动
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    retry_count = db.Column(db.Integer, default=0, comment='重试次数')

    # 关联
    logs = db.relationship('TaskLog', backref=db.backref('task', lazy=True))
    source_client = db.relationship('Client', foreign_keys=[source_client_id], backref='source_tasks')
    source_storage = db.relationship('Storage', foreign_keys=[source_storage_id], backref='source_tasks')
    target_storage = db.relationship('Storage', foreign_keys=[target_storage_id], backref='target_tasks')
    
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
            'node_id': self.node_id,
            'source_type': self.source_type,
            'source_client_id': self.source_client_id,
            'source_storage_id': self.source_storage_id,
            'source_path': self.source_path,
            'target_storage_id': self.target_storage_id,
            'target_path': self.target_path,
            'retry_count': self.retry_count,
        })
        return data

    def to_dict_with_storage_config(self):
        """转换为字典，包含存储配置信息（供proxy使用）"""
        data = self.to_dict()
        
        # 添加源端存储配置
        if self.source_storage and self.source_storage_id:
            data['source_storage_config'] = {
                'id': self.source_storage.id,
                'name': self.source_storage.name,
                'type': self.source_storage.type,
                'config': self.source_storage.config,
                'status': self.source_storage.status
            }
        
        # 添加客户端配置
        if self.source_client and self.source_client_id:
            data['source_client_config'] = {
                'id': self.source_client.id,
                'name': self.source_client.name,
                'hostname': self.source_client.hostname,
                'ip_address': self.source_client.ip_address,
                'port': self.source_client.port,
                'username': self.source_client.username,
                'auth_type': self.source_client.auth_type,
                'status': self.source_client.status
            }
        
        # 添加目标端存储配置
        if self.target_storage and self.target_storage_id:
            data['target_storage_config'] = {
                'id': self.target_storage.id,
                'name': self.target_storage.name,
                'type': self.target_storage.type,
                'config': self.target_storage.config,
                'status': self.target_storage.status
            }
        
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