from flask import Blueprint

monitor_bp = Blueprint('monitor', __name__, url_prefix='')

from . import routes
from . import scheduler 