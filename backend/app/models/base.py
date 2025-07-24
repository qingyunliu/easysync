import uuid
from datetime import datetime
from backend import db

class BaseModel(db.Model):
    """基础模型类"""
    __abstract__ = True
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SystemSetting(BaseModel):
    """全局系统设置表，key-value 结构，value 可为字符串或 JSON"""
    __tablename__ = 'system_settings'
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    @staticmethod
    def get_json(key, default=None):
        from backend import db
        s = db.session.query(SystemSetting).filter_by(key=key).first()
        if s:
            import json
            try:
                return json.loads(s.value)
            except Exception:
                return default
        return default

    @staticmethod
    def set_json(key, value):
        from backend import db
        import json
        s = db.session.query(SystemSetting).filter_by(key=key).first()
        if not s:
            s = SystemSetting(key=key, value=json.dumps(value, ensure_ascii=False))
            db.session.add(s)
        else:
            s.value = json.dumps(value, ensure_ascii=False)
        db.session.commit()