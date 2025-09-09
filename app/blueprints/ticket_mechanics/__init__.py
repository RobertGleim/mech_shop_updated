from flask import Blueprint



ticket_mechanics_bp = Blueprint('ticket_mechanics_bp', __name__)

from . import route