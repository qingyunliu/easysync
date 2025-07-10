from enum import Enum
from backend.app.models.base import BaseModel
from backend import db


class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"

class AgentStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"

class Node(BaseModel):
    """节点模型，支持分组、标签等运维属性"""
    __tablename__ = 'nodes'
    
    name = db.Column(db.String(100), nullable=False)
    ipaddress = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    auth_type = db.Column(db.String(20), default='password')
    auth_key = db.Column(db.String(255))
    status = db.Column(db.String(20), default=NodeStatus.OFFLINE.value)
    config = db.Column(db.JSON)  # 节点配置信息
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    last_heartbeat = db.Column(db.DateTime)
    agent_status = db.Column(db.String(20), default=AgentStatus.INACTIVE.value)  # INACTIVE, ACTIVE, ERROR
    agent_version = db.Column(db.String(32))  # ProxyAgent版本
    agent_last_update = db.Column(db.DateTime)  # ProxyAgent最后更新时间
    system_info = db.Column(db.JSON)  # 系统信息（OS、CPU、内存等）
    description = db.Column(db.String(255)) # 描述信息
    group = db.Column(db.String(64), default='default', comment='分组')  # 节点分组
    tags = db.Column(db.Text, comment='标签，逗号分隔')  # 节点标签

    tasks = db.relationship('Task', backref=db.backref('node', lazy=True))
    storage = db.relationship('Storage', backref=db.backref('node', lazy=True))

    __table_args__ = {
        'comment': '节点表，含分组、标签等运维属性'
    }

    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'username': self.username,
            'ipaddress': self.ipaddress,
            'port': self.port,
            'status': self.status,
            'description': self.description,
            'config': self.config,
            'user_id': self.user_id,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'agent_status': self.agent_status,
            'agent_version': self.agent_version,
            'agent_last_update': self.agent_last_update.isoformat() if self.agent_last_update else None,
            'system_info': self.system_info,
            'group': self.group,
            'tags': self.tags
        })
        return data
