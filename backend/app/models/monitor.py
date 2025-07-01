from datetime import datetime, timedelta
from backend import db
from backend.app.models.base import BaseModel
from sqlalchemy import CheckConstraint

class MonitorData(BaseModel):
    """监控数据模型"""
    __tablename__ = 'monitor_data'
    
    # 添加索引和约束
    __table_args__ = (
        db.Index('idx_monitor_timestamp', 'timestamp'),
        db.Index('idx_monitor_client', 'client_id'),
        db.Index('idx_monitor_node', 'node_id'),
        CheckConstraint('client_id IS NOT NULL OR node_id IS NOT NULL', 
                       name='check_client_or_node'),
    )
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=True)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data = db.Column(db.JSON)
    
    # 添加关联关系
    client = db.relationship('Client', backref=db.backref('monitor_data', lazy=True))
    node = db.relationship('Node', backref=db.backref('monitor_data', lazy=True))
    
    def to_dict(self):
        """转换为字典"""
        return {
             'id': self.id,
             'user_id': self.user_id,
             'client_id': self.client_id,
             'timestamp': self.timestamp.isoformat(),
             'data': self.data
        }
    
    @staticmethod
    def create_monitor_data(user_id=None, client_id=None, node_id=None, data=None):
        """创建新的监控数据记录
        
        Args:
            user_id: 用户ID
            client_id: 客户端ID（可选）
            node_id: 节点ID（可选）
            data: 监控数据（JSON格式）
            
        Returns:
            MonitorData: 创建的监控数据记录
            
        Raises:
            ValueError: 当client_id和node_id都为空时
        """
        if not client_id and not node_id:
            raise ValueError("Either client_id or node_id must be provided")
            
        try:
            monitor_data = MonitorData(
                user_id=user_id,
                client_id=client_id,
                node_id=node_id,
                data=data,
                timestamp=datetime.utcnow()
            )
            db.session.add(monitor_data)
            db.session.commit()
            return monitor_data
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_by_client(cls, client_id, start_time=None, end_time=None):
        """获取指定客户端的监控数据
        
        Args:
            client_id: 客户端ID
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
        """
        query = cls.query.filter_by(client_id=client_id)
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_by_node(cls, node_id, start_time=None, end_time=None):
        """获取指定节点的监控数据"""
        query = cls.query.filter_by(node_id=node_id)
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def cleanup_old_data(cls, days=30):
        """清理指定天数前的旧数据
        
        Args:
            days: 保留天数
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        try:
            cls.query.filter(cls.timestamp < cutoff_date).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class PerformanceMetric(BaseModel):
    """性能指标模型"""
    __tablename__ = 'performance_metrics'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'))
    
    # 关联
    task = db.relationship('Task', backref=db.backref('performance_metrics', lazy=True))
    node = db.relationship('Node', backref=db.backref('performance_metrics', lazy=True))
    owner = db.relationship('User', foreign_keys=[user_id], backref=db.backref('performance_metrics', lazy=True))
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'task_id': self.task_id,
            'metric_type': self.metric_type,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'node_id': self.node_id
        })
        return data