from flask import Blueprint

invoice = Blueprint('invoice_bp', __name__)  

from . import route