from flask import Blueprint

item_descriptions_bp = Blueprint('item_descriptions_bp', __name__)  

from . import route