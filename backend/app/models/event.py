from datetime import datetime
from backend import db
from backend.app.models.base import BaseModel
from sqlalchemy import CheckConstraint

class Event(BaseModel):
    """事件模型 - 存储系统事件"""
    __tablename__ = 'events'
    
    # 添加索引和约束
    __table_args__ = (
        db.Index('idx_event_timestamp', 'timestamp'),
        db.Index('idx_event_type', 'event_type'),
        db.Index('idx_event_action', 'event_action'),
        db.Index('idx_event_result', 'event_result'),
        CheckConstraint('(client_id IS NOT NULL OR node_id IS NOT NULL) OR (client_id IS NULL AND node_id IS NULL)', 
                       name='check_event_client_or_node'),
    )
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=True)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    
    # 事件信息
    event_type = db.Column(db.String(50), nullable=False, comment='事件类型: storage, client, agent, system')
    event_action = db.Column(db.String(50), nullable=False, comment='事件动作: create, delete, update, connect, disconnect等')
    event_result = db.Column(db.String(20), nullable=False, comment='事件结果: success, failed, timeout, error, warning')
    
    # 事件详情
    message = db.Column(db.Text, comment='事件消息')
    details = db.Column(db.JSON, comment='事件详细信息')
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 关联关系
    client = db.relationship('Client', backref=db.backref('events', lazy=True))
    node = db.relationship('Node', backref=db.backref('events', lazy=True))
    user = db.relationship('User', backref=db.backref('events', lazy=True))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'client_id': self.client_id,
            'node_id': self.node_id,
            'event_type': self.event_type,
            'event_action': self.event_action,
            'event_result': self.event_result,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_event(user_id=None, client_id=None, node_id=None, event_type=None, 
                    event_action=None, event_result=None, message=None, details=None):
        """创建新的事件记录
        
        Args:
            user_id: 用户ID
            client_id: 客户端ID（可选）
            node_id: 节点ID（可选）
            event_type: 事件类型
            event_action: 事件动作
            event_result: 事件结果
            message: 事件消息
            details: 事件详情
            
        Returns:
            Event: 创建的事件记录
        """
        try:
            event = Event(
                user_id=user_id,
                client_id=client_id,
                node_id=node_id,
                event_type=event_type,
                event_action=event_action,
                event_result=event_result,
                message=message,
                details=details,
                timestamp=datetime.utcnow()
            )
            db.session.add(event)
            db.session.commit()
            return event
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_by_type(cls, event_type, start_time=None, end_time=None):
        """获取指定类型的事件"""
        query = cls.query.filter_by(event_type=event_type)
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_by_action(cls, event_action, start_time=None, end_time=None):
        """获取指定动作的事件"""
        query = cls.query.filter_by(event_action=event_action)
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_by_result(cls, event_result, start_time=None, end_time=None):
        """获取指定结果的事件"""
        query = cls.query.filter_by(event_result=event_result)
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_by_resource(cls, resource_id, resource_type='node', start_time=None, end_time=None):
        """获取指定资源的事件"""
        if resource_type == 'node':
            query = cls.query.filter_by(node_id=resource_id)
        elif resource_type == 'client':
            query = cls.query.filter_by(client_id=resource_id)
        else:
            return []
        
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def cleanup_old_events(cls, days=30):
        """清理指定天数前的旧事件"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        try:
            cls.query.filter(cls.timestamp < cutoff_date).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e 