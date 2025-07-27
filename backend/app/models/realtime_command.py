# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from backend import db
from .base import BaseModel


class RealTimeCommand(BaseModel):
    """实时命令模型"""
    
    __tablename__ = 'realtime_commands'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    command_type = db.Column(db.String(50), nullable=False)  # test_connection, list_files, get_stats, download_file
    params = db.Column(db.JSON, nullable=False, default=dict)
    status = db.Column(db.String(20), default='pending')  # pending, executing, completed, failed, timeout
    result = db.Column(db.JSON, default=dict)
    error = db.Column(db.Text)
    timeout = db.Column(db.Integer, default=30)  # 超时时间（秒）
    priority = db.Column(db.Integer, default=1)  # 优先级，1最高
    
    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    node = db.relationship('Node', backref='realtime_commands')
    user = db.relationship('User', backref='realtime_commands')
    
    def __repr__(self):
        return f'<RealTimeCommand {self.id}: {self.command_type} -> {self.status}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'user_id': self.user_id,
            'command_type': self.command_type,
            'params': self.params,
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'timeout': self.timeout,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'execution_time': self.get_execution_time()
        }
    
    def get_execution_time(self):
        """获取执行时间（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None
    
    def is_expired(self):
        """检查命令是否超时"""
        if self.status in ['completed', 'failed', 'timeout']:
            return False
        
        if self.created_at:
            elapsed = (datetime.utcnow() - self.created_at).total_seconds()
            return elapsed > self.timeout
        return False
    
    def mark_as_executing(self):
        """标记为执行中"""
        self.status = 'executing'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self, result=None):
        """标记为已完成"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if result:
            self.result = result
    
    def mark_as_failed(self, error=None):
        """标记为失败"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if error:
            self.error = str(error)
    
    def mark_as_timeout(self):
        """标记为超时"""
        self.status = 'timeout'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error = f'Command timed out after {self.timeout} seconds'
    
    @classmethod
    def create_command(cls, node_id, user_id, command_type, params, timeout=30, priority=1):
        """创建实时命令"""
        command = cls(
            node_id=node_id,
            user_id=user_id,
            command_type=command_type,
            params=params,
            timeout=timeout,
            priority=priority
        )
        db.session.add(command)
        db.session.commit()
        return command
    
    @classmethod
    def get_pending_commands(cls, node_id):
        """获取节点的待执行命令（按优先级和创建时间排序）"""
        return cls.query.filter_by(
            node_id=node_id, 
            status='pending'
        ).order_by(
            cls.priority.asc(),  # 优先级升序（1最高）
            cls.created_at.asc()  # 创建时间升序
        ).all()
    
    @classmethod
    def cleanup_expired_commands(cls):
        """清理过期的命令"""
        expired_commands = cls.query.filter(
            cls.status.in_(['pending', 'executing'])
        ).all()
        
        count = 0
        for command in expired_commands:
            if command.is_expired():
                command.mark_as_timeout()
                count += 1
        
        if count > 0:
            db.session.commit()
        
        return count