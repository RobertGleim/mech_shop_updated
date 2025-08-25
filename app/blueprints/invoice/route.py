from . import invoice_bp
from .schema import invoice_schema, invoices_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Invoice, db, InventoryItem
from app.extenstions import limiter, cache




@invoice_bp.route('/', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
def create_invoice():
    try:
        data = invoice_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    
    new_invoice = Invoice(**data)
    db.session.add(new_invoice)
    db.session.commit()
    
    return invoice_schema.jsonify(new_invoice), 201

#  =========================================================================
@invoice_bp.route('/', methods=['GET'])
# limiter left blank to use default limits
@cache.cached(timeout=30)
def read_invoices():
    invoices = db.session.query(Invoice).all()
    return invoices_schema.jsonify(invoices), 200

#  =========================================================================

@invoice_bp.route('/<int:id>', methods=['GET'])
@limiter.limit("30 per hour", override_defaults=True)
def read_invoice(id):
   
   invoice = db.session.query(Invoice).where(Invoice.id==id).first()
   return invoice_schema.jsonify(invoice), 200

#  =========================================================================

@invoice_bp.route('/<int:id>', methods=['DELETE'])
@limiter.limit("5 per hour", override_defaults=True)
def delete_invoice(id):
    invoice = db.session.query(Invoice).where(Invoice.id==id).first()
    if not invoice:
        return jsonify({"message": "Invoice not found"}), 404
    
    db.session.delete(invoice)
    db.session.commit()
    return jsonify({"message": f"Invoice {id} deleted"}), 200

#  =========================================================================

@invoice_bp.route('/<int:id>', methods=['PUT'])
@limiter.limit("10 per hour", override_defaults=True)
def update_invoice(id):
    invoice = db.session.query(Invoice).where(Invoice.id==id).first()
    if not invoice:
        return jsonify({"message": "Invoice not found"}), 404
    
    try:
        data = invoice_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for key, value in data.items():
        setattr(invoice, key, value)
    
    db.session.commit()
    return invoice_schema.jsonify(invoice), 200


#  =========================================================================

@invoice_bp.route('/<int:invoice_id>', methods=['DELETE'])
@limiter.limit("5 per hour", override_defaults=True)
def delete_invoice_item(invoice_id):
    
    invoice_item = db.session.query(InventoryItem).where(InventoryItem.invoice_id==invoice_id).first()
    
    if not invoice_item:
        return jsonify({"message": "Invoice item not found"}), 404
    
    db.session.delete(invoice_item)
    db.session.commit()
    return jsonify({"message": f"Invoice item {invoice_id} deleted"}), 200

#  =========================================================================
@invoice_bp.route('/<int:invoice_id>'/'update_invoice_item', methods=['PUT'])
@limiter.limit("10 per hour", override_defaults=True)
def update_invoice_item(invoice_id):
            
    invoice_item = db.session.query(InventoryItem).where(InventoryItem.invoice_id==invoice_id).first()
    
    if not invoice_item:
        return jsonify({"message": "Invoice item not found"}), 404
    
    try:
        data = invoice_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for key, value in data.items():
        setattr(invoice_item, key, value)
    
    db.session.commit()
    return invoice_schema.jsonify(invoice_item), 200

#  =========================================================================

@invoice_bp.route('/<int:invoice_id>/add_item', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
def add_invoice_item(invoice_id):
    try:
        data = invoice_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    
    new_invoice_item = InventoryItem(invoice_id=invoice_id, **data)
    db.session.add(new_invoice_item)
    db.session.commit()
    
    return invoice_schema.jsonify(new_invoice_item), 201

#  =========================================================================

