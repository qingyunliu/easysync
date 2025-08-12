"""
事件模块
提供事件记录、管理和告警功能
"""

from flask import Blueprint

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

from . import routes