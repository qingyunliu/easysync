from flask import Blueprint

commands_bp = Blueprint('commands', __name__, url_prefix='')

from . import routes 