from flask import Blueprint

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

from . import routes 