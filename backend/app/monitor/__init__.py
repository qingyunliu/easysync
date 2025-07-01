from flask import Blueprint

monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')

from . import routes 