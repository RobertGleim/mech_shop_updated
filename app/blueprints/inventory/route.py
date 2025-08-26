from . import inventory_bp
from .schema import inventory_schema, inventories_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import InventoryItem, db, ItemsDescription
from app.extenstions import limiter, cache




@inventory_bp.route('/', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
def create_inventory_item():
    try:
        data = inventory_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    
    new_inventory_item = InventoryItem(**data)
    db.session.add(new_inventory_item)
    db.session.commit()
    
    return inventory_schema.jsonify(new_inventory_item), 201

#  =========================================================================

@inventory_bp.route('/', methods=['GET'])
# limiter left blank to use default limits
@cache.cached(timeout=30)
def get_inventory_items():
    inventory_items = db.session.query(InventoryItem).all()
    return inventories_schema.jsonify(inventory_items), 200

#  =========================================================================

@inventory_bp.route('/<int:id>', methods=['GET'])
@limiter.limit("30 per hour", override_defaults=True)
def get_inventory_item(id):
   
   inventory = db.session.query(InventoryItem).where(InventoryItem.id==id).first()
   return inventory_schema.jsonify(inventory), 200

#  =========================================================================

@inventory_bp.route('/<int:id>', methods=['DELETE'])
@limiter.limit("5 per hour", override_defaults=True)    
def delete_inventory_item(id):
    inventory_item = db.session.query(InventoryItem).where(InventoryItem.id==id).first()
    if not inventory_item:
        return jsonify({"message": "Inventory item not found"}), 404
    
    db.session.delete(inventory_item)
    db.session.commit()
    return jsonify({"message": f"Inventory item {id} deleted"}), 200

#  =========================================================================

@inventory_bp.route('/<int:id>', methods=['PUT'])
@limiter.limit("10 per hour", override_defaults=True)
def update_inventory_item(id):
    inventory_item = db.session.query(InventoryItem).where(InventoryItem.id==id).first()
    if not inventory_item:
        return jsonify({"message": "Inventory item not found"}), 404
    try:
        inventory_data = inventory_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    for key, value in inventory_data.items():
        setattr(inventory_item, key, value)
    
    db.session.commit()
    return inventory_schema.jsonify(inventory_item), 200

#  =========================================================================


@inventory_bp.route('/search', methods=['GET'])
@limiter.limit("30 per hour", override_defaults=True)   
def search_inventory_items():
    part_name = request.args.get('part_name')
    part_desc = request.args.get('part_desc')
    
    query = db.session.query(ItemsDescription)
    
    if part_name:
        query = query.filter(ItemsDescription.part_name.ilike(f'%{part_name}%'))
    if part_desc:
        query = query.filter(ItemsDescription.part_desc.ilike(f'%{part_desc}%'))
    
    results = query.all()
    
    return jsonify(inventories_schema.dump(results)), 200

#  =========================================================================

