from backend.app.models.base import BaseModel
from backend import db

class Storage(BaseModel):
    """存储节点模型"""
    __tablename__ = 'storages'
    
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # local, s3, ftp
    config = db.Column(db.JSON)  # 存储配置信息（如S3的access key等）
    status = db.Column(db.String(20), default='active')  # active, error, disabled
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'))

    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'type': self.type,
            'config': self.config,
            'status': self.status,
            'user_id': self.user_id,
            'node_id': self.node_id
        })
        return data