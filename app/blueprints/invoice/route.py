from . import invoice_bp
from .schema import invoice_schema, invoices_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Invoice, Invoice_Inventory_Link, db, InventoryItem
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
def get_invoices():
    invoices = db.session.query(Invoice).all()
    return invoices_schema.jsonify(invoices), 200

#  =========================================================================

@invoice_bp.route('/<int:id>', methods=['GET'])
@limiter.limit("30 per hour", override_defaults=True)
def get_invoice(id):
   
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
 
@invoice_bp.route('/<int:invoice_id>/add_invoice_item', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
def add_invoice_item(invoice_id):
    invoice = db.session.query(Invoice).get(invoice_id)
    if not invoice:
        return jsonify({"message": "Invoice not found"}), 404

    data = request.json
    quantity = data.get("quantity", 1)  

    try:
        inventory_item_id = int(data.get("inventory_item_id"))
    except (TypeError, ValueError):
        return jsonify({"message": "inventory_item_id must be an integer"}), 400

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({"message": "quantity must be an integer"}), 400
    
    
    if not inventory_item_id:
        return jsonify({"message": "inventory_item_id is required"}), 400

    inventory_item = db.session.query(InventoryItem).get(inventory_item_id)
    if not inventory_item:
        return jsonify({"message": "Inventory item not found"}), 404

    
    link = db.session.query(Invoice_Inventory_Link).filter_by(
        invoice_id=invoice_id, inventory_item_id=inventory_item_id).first()
    
    if link:
        
        link.quantity += quantity
    else:
       
        link = Invoice_Inventory_Link(invoice=invoice, inventory_item=inventory_item, quantity=quantity)
        db.session.add(link)

    db.session.commit()

    return jsonify({
        "message": f"Inventory item {inventory_item_id} added to invoice {invoice_id}",
        "quantity": link.quantity
    }), 201 

#  =========================================================================

@invoice_bp.route('/<int:invoice_id>/delete_invoice_item/<int:inventory_item_id>', methods=['DELETE'])
@limiter.limit("5 per hour", override_defaults=True)
def delete_invoice_item(invoice_id, inventory_item_id):
    link = db.session.query(Invoice_Inventory_Link).filter_by(
        invoice_id=invoice_id, inventory_item_id=inventory_item_id
    ).first()

    if not link:
        return jsonify({"message": "Invoice item not found"}), 404

    db.session.delete(link)
    db.session.commit()
    return jsonify({"message": f"Inventory item {inventory_item_id} removed from invoice {invoice_id}"}), 200
#  =========================================================================
@invoice_bp.route('/<int:invoice_id>/update_invoice_item/<int:inventory_item_id>', methods=['PUT'])
@limiter.limit("10 per hour", override_defaults=True)
def update_invoice_item(invoice_id, inventory_item_id):
    link = db.session.query(Invoice_Inventory_Link).filter_by(
        invoice_id=invoice_id, inventory_item_id=inventory_item_id
    ).first()

    if not link:
        return jsonify({"message": "Invoice item not found"}), 404

    data = request.json
    new_inventory_item_id = data.get("inventory_item_id")
    if not new_inventory_item_id:
        return jsonify({"message": "inventory_item_id is required to update"}), 400

    new_item = db.session.query(InventoryItem).get(new_inventory_item_id)
    if not new_item:
        return jsonify({"message": "New inventory item not found"}), 404

   
    link.inventory_item = new_item
    db.session.commit()

    return jsonify({"message": f"Inventory item {inventory_item_id} replaced with {new_inventory_item_id} for invoice {invoice_id}"}), 200

#  =========================================================================





