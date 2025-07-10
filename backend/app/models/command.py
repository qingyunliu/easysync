from backend import db
import uuid
from datetime import datetime

class Command(db.Model):
    __tablename__ = 'commands'
    id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = db.Column(db.String(64), db.ForeignKey('nodes.id'), nullable=False)
    type = db.Column(db.String(32), nullable=False)  # shell/python/upgrade等
    command = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), default='pending')  # pending/running/completed/failed
    result = db.Column(db.JSON, nullable=True)
    timeout = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Command {self.id} {self.type} {self.status}>' 