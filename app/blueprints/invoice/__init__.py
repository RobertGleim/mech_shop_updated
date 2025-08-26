from flask import Blueprint

invoice_bp = Blueprint('invoice_bp', __name__)  

from . import route