from flask import Blueprint

storages_bp = Blueprint('storages', __name__, url_prefix='')

from . import routes 