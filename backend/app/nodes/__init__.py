from flask import Blueprint

nodes_bp = Blueprint('nodes', __name__, url_prefix='')

from . import routes 