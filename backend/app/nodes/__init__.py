from flask import Blueprint

nodes_bp = Blueprint('nodes', __name__, url_prefix='/api/nodes')

from . import routes 