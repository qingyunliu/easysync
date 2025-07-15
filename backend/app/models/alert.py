from datetime import datetime
from backend import db
from backend.app.models.base import BaseModel
import enum


class AlertLevel(enum.Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(enum.Enum):
    """告警状态"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

class Alert(BaseModel):
    """告警模型"""
    __tablename__ = 'alerts'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=True)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    rule_id = db.Column(db.String(36), db.ForeignKey('alert_rules.id'), nullable=True)
    alert_type = db.Column(db.String(50), nullable=False)  # cpu_high, memory_high, disk_high, load_high, etc.
    metric = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    level = db.Column(db.Enum(AlertLevel), nullable=False, default=AlertLevel.WARNING)
    severity = db.Column(db.String(20), nullable=False)  # 保持兼容性
    message = db.Column(db.Text)
    status = db.Column(db.Enum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    resolved_at = db.Column(db.DateTime, nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 关联
    rule = db.relationship('AlertRule', backref=db.backref('alerts', lazy=True))
    client = db.relationship('Client', backref=db.backref('alerts', lazy=True))
    node = db.relationship('Node', backref=db.backref('alerts', lazy=True))
    user = db.relationship('User', backref=db.backref('alerts', lazy=True))
    
    # 索引
    __table_args__ = (
        db.Index('idx_node_status', 'node_id', 'status'),
        db.Index('idx_user_level', 'user_id', 'level'),
        db.Index('idx_timestamp', 'timestamp'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'client_id': self.client_id,
            'node_id': self.node_id,
            'rule_id': self.rule_id,
            'alert_type': self.alert_type,
            'metric': self.metric,
            'value': self.value,
            'threshold': self.threshold,
            'level': self.level.value if self.level else None,
            'severity': self.severity,
            'message': self.message,
            'status': self.status.value if self.status else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_active_alerts(cls, user_id=None, node_id=None, limit=100):
        """获取活跃告警"""
        query = cls.query.filter_by(status=AlertStatus.ACTIVE)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        if node_id:
            query = query.filter_by(node_id=node_id)
            
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_alerts_by_type(cls, alert_type, user_id=None, limit=50):
        """根据类型获取告警"""
        query = cls.query.filter_by(alert_type=alert_type)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def resolve_alert(cls, alert_id, user_id=None):
        """解决告警"""
        alert = cls.query.get(alert_id)
        if not alert:
            return False
            
        if user_id and alert.user_id != user_id:
            return False
            
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    @classmethod
    def acknowledge_alert(cls, alert_id, acknowledged_by, user_id=None):
        """确认告警"""
        alert = cls.query.get(alert_id)
        if not alert:
            return False
            
        if user_id and alert.user_id != user_id:
            return False
            
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        alert.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    @classmethod
    def get_alert_summary(cls, user_id=None):
        """获取告警汇总"""
        query = cls.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        # 统计各状态的告警数量
        active_count = query.filter_by(status=AlertStatus.ACTIVE).count()
        resolved_count = query.filter_by(status=AlertStatus.RESOLVED).count()
        acknowledged_count = query.filter_by(status=AlertStatus.ACKNOWLEDGED).count()
        
        # 统计各级别的告警数量
        critical_count = query.filter_by(level=AlertLevel.CRITICAL, status=AlertStatus.ACTIVE).count()
        warning_count = query.filter_by(level=AlertLevel.WARNING, status=AlertStatus.ACTIVE).count()
        info_count = query.filter_by(level=AlertLevel.INFO, status=AlertStatus.ACTIVE).count()
        
        return {
            'status_summary': {
                'active': active_count,
                'resolved': resolved_count,
                'acknowledged': acknowledged_count,
                'total': active_count + resolved_count + acknowledged_count
            },
            'level_summary': {
                'critical': critical_count,
                'warning': warning_count,
                'info': info_count
            }
        }

class AlertRule(BaseModel):
    """告警规则模型"""
    __tablename__ = 'alert_rules'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    metric = db.Column(db.String(50), nullable=False)
    operator = db.Column(db.String(20), nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'description': self.description,
            'metric': self.metric,
            'operator': self.operator,
            'threshold': self.threshold,
            'duration': self.duration,
            'severity': self.severity,
            'enabled': self.enabled
        }