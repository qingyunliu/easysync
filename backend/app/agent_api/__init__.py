from flask import Blueprint

agent_bp = Blueprint('agent_bp', __name__, url_prefix='/api/agent')

from . import routes 