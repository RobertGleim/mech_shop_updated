from . import service_tickets_bp
from .schema import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Mechanics, Service_Ticket, db
from app.extenstions import limiter,cache
from app.util.auth import token_required, role_required 
from sqlalchemy import func

 #  =========================================================================
 
@service_tickets_bp.route('/', methods=['POST'])
@limiter.limit("20 per hour")
def create_service_ticket():
    try:
        data = service_ticket_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400

    new_service = Service_Ticket(**data)
    db.session.add(new_service)
    db.session.commit()
    print(f"New Service ticket was created : For Customer {new_service.customer_id}")
    return service_ticket_schema.jsonify(new_service), 201

 #  =========================================================================
 

@service_tickets_bp.route('/', methods=['GET'])
@limiter.limit("50 per hour")
@cache.cached(timeout=30)
@token_required
@role_required(['admin', 'mechanic'])
def get_service_tickets(user_id, role):
    service_tickets = db.session.query(Service_Ticket).all()
    return service_tickets_schema.jsonify(service_tickets), 200

 #  =========================================================================

@service_tickets_bp.route('/<int:service_tickets_id>', methods=['GET'])
@limiter.limit("50 per hour")
@cache.cached(timeout=30)
@token_required
@role_required(['admin', 'mechanic'])
def get_service_ticket(user_id, role, service_tickets_id):
    service_ticket = db.session.get(Service_Ticket, service_tickets_id) 
    print(f"Service Ticket found: {service_tickets_id}")
    return service_ticket_schema.jsonify(service_ticket), 200

 #  =========================================================================

@service_tickets_bp.route('/<int:service_tickets_id>', methods=['DELETE'])
@limiter.limit("3 per hour")
@token_required
@role_required(['admin', 'mechanic'])
def delete_service_ticket(user_id, role, service_tickets_id):
    service_ticket = db.session.get(Service_Ticket, service_tickets_id)
    if not service_ticket:
        return jsonify({"message": "Service Ticket not found"}), 404    
    db.session.delete(service_ticket)
    db.session.commit()
   
    return jsonify({"message": f"Service Ticket  {service_tickets_id} was deleted "}), 200

 #  =========================================================================

@service_tickets_bp.route('/<int:service_ticket_id>', methods=['PUT'])
@limiter.limit("20 per hour", override_defaults=True)
@token_required
@role_required(['admin', 'mechanic'])
def update_service_ticket(user_id, role, service_ticket_id):
    service_ticket = db.session.get(Service_Ticket, service_ticket_id)
    
    if not service_ticket:
        return jsonify({"message": "Service Ticket not found"}), 404
    try:
        service_ticket_data = service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"Message": e.messages}), 400
    for key, value in service_ticket_data.items():
        setattr(service_ticket, key, value)
    db.session.commit()
    
    return service_ticket_schema.jsonify(service_ticket), 200

# ==========================================================================

@service_tickets_bp.route('/popular', methods=['GET'])
@limiter.limit("10 per hour")
@cache.cached(timeout=30)  
@token_required
@role_required(['admin'])
def popular_service_tickets(user_id, role):
    
    popular_tickets = (
        db.session.query(Service_Ticket.service_description,func.count(Service_Ticket.id).label('usage_count'))
        .group_by(Service_Ticket.service_description)
        .order_by(func.count(Service_Ticket.id).desc()).limit(3).all())

    ticket_data = [
        {"service_description": ticket.service_description,"usage_count": ticket.usage_count}
        for ticket in popular_tickets]
    
    return jsonify(ticket_data), 200

