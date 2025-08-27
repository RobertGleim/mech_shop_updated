from flask import Blueprint

invoice_inventory_link_bp = Blueprint('invoice_inventory_link_bp', __name__)  

from . import route