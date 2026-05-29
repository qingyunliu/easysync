from flask import Blueprint

alerts_bp = Blueprint('alerts', __name__, url_prefix='')

from . import routes