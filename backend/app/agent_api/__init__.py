from flask import Blueprint

agent_bp = Blueprint('agent_bp', __name__, url_prefix='/api/proxy/v1/nodes')

from . import routes 