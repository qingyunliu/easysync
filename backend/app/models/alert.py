from datetime import datetime
from backend import db
from backend.app.models.base import BaseModel

class Alert(BaseModel):
    """告警模型"""
    __tablename__ = 'alerts'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=True)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    rule_id = db.Column(db.String(36), db.ForeignKey('alert_rules.id'), nullable=False)
    metric = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)
    
    # 关联
    rule = db.relationship('AlertRule', backref=db.backref('alerts', lazy=True))
    client = db.relationship('Client', backref=db.backref('alerts', lazy=True))
    node = db.relationship('Node', backref=db.backref('alerts', lazy=True))
    user = db.relationship('User', backref=db.backref('alerts', lazy=True))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'client_id': self.client_id,
            'node_id': self.node_id,
            'rule_id': self.rule_id,
            'metric': self.metric,
            'value': self.value,
            'threshold': self.threshold,
            'severity': self.severity,
            'message': self.message
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