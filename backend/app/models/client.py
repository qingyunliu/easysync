from backend import db
from backend.app.models.base import BaseModel

class Client(BaseModel):
    """服务器模型"""
    __tablename__ = 'clients'
    
    name = db.Column(db.String(64), nullable=False)
    hostname = db.Column(db.String(128))
    ip_address = db.Column(db.String(45), nullable=False)
    port = db.Column(db.Integer, default=22)
    username = db.Column(db.String(64), nullable=False)
    auth_type = db.Column(db.String(20), default='password')
    password = db.Column(db.String(128))
    ssh_key = db.Column(db.Text)
    status = db.Column(db.String(20), default='offline')
    agent_status = db.Column(db.String(20), default='not_installed')
    agent_version = db.Column(db.String(32))
    last_seen = db.Column(db.DateTime)
    os_type = db.Column(db.String(32))
    os_version = db.Column(db.String(32))
    cpu_info = db.Column(db.String(256))
    memory_info = db.Column(db.String(256))
    disk_info = db.Column(db.Text)
    network_info = db.Column(db.Text)
    description = db.Column(db.Text)
    
    # 外键关系
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'port': self.port,
            'username': self.username,
            'auth_type': self.auth_type,
            'status': self.status,
            'agent_status': self.agent_status,
            'agent_version': self.agent_version,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'os_type': self.os_type,
            'os_version': self.os_version,
            'cpu_info': self.cpu_info,
            'memory_info': self.memory_info,
            'disk_info': self.disk_info,
            'network_info': self.network_info,
            'description': self.description
        })
        return data