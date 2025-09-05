from . import item_descriptions_bp
from .schema import item_description_schema, item_descriptions_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import InventoryItem, ItemsDescription, db
from app.extenstions import limiter, cache








@item_descriptions_bp.route('/', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
def create_item_description():
    try:
        data = item_description_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    
    new_item_description = ItemsDescription(**data)
    db.session.add(new_item_description)
    db.session.commit()
    
    return item_description_schema.jsonify(new_item_description), 201

#  =========================================================================

@item_descriptions_bp.route('/', methods=['GET'])
# limiter left blank to use default limits
@cache.cached(timeout=30)
def get_item_descriptions():
    item_descriptions_bp = db.session.query(ItemsDescription).all()
    return item_descriptions_schema.jsonify(item_descriptions_bp), 200

#  =========================================================================

@item_descriptions_bp.route('/<int:id>', methods=['GET'])
@limiter.limit("30 per hour", override_defaults=True)
def get_item_description(id):
    item_description = db.session.query(ItemsDescription).where(ItemsDescription.id==id).first()
    if not item_description:
        return jsonify({"message": "Item description not found"}), 404
    return item_description_schema.jsonify(item_description), 200

#  =========================================================================

@item_descriptions_bp.route('/<int:id>', methods=['DELETE'])
@limiter.limit("5 per hour", override_defaults=True)    
def delete_item_description(id):
    item_description = db.session.query(ItemsDescription).where(ItemsDescription.id==id).first()
    if not item_description:
        return jsonify({"message": "Item description not found"}), 404
    
    db.session.delete(item_description)
    db.session.commit()
    return jsonify({"message": f"Item description {id} deleted"}), 200

#  =========================================================================

@item_descriptions_bp.route('/<int:id>', methods=['PUT'])
@limiter.limit("10 per hour", override_defaults=True)
def update_item_descriptions(id):
    inventory_item = db.session.query(InventoryItem).where(InventoryItem.id==id).first()
    if not inventory_item:
        return jsonify({"message": "Inventory item not found"}), 404
    try:
        item_description_data = item_description_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    for key, value in item_description_data.items():
        setattr(inventory_item, key, value)
    
    db.session.commit()
    return item_description_schema.jsonify(inventory_item), 200

#  =========================================================================

def item_names(self):
    return f"{self.part_name}"