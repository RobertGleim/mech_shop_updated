from . import service_tickets_bp
from .schema import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Mechanics, Service_Ticket, db
from app.extenstions import limiter,cache
from app.util.auth import token_required 

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
@limiter.limit("50 per hour" )
@cache.cached(timeout=30)
def read_service_tickets():
    service_tickets = db.session.query(Service_Ticket).all()
    return service_tickets_schema.jsonify(service_tickets), 200

 #  =========================================================================

@service_tickets_bp.route('/<int:service_tickets_id>', methods=['GET'])
@limiter.limit("50 per hour")
@cache.cached(timeout=30)
def read_service_ticket(service_tickets_id):
    service_ticket = db.session.get(Service_Ticket, service_tickets_id) 
    print(f"Service Ticket found: {service_tickets_id}")
    return service_ticket_schema.jsonify(service_ticket), 200

 #  =========================================================================

@service_tickets_bp.route('/<int:service_tickets_id>', methods=['DELETE'])
@limiter.limit("3 per hour")  
def delete_service_ticket(service_tickets_id):
    service_ticket = db.session.get(Service_Ticket, service_tickets_id)
    if not service_ticket:
        return jsonify({"message": "Service Ticket not found"}), 404    
    db.session.delete(service_ticket)
    db.session.commit()
    print(f"Service Ticket {service_tickets_id} was deleted ")
    return jsonify({"message": f"Service Ticket  {service_tickets_id} was deleted "}), 200

 #  =========================================================================

@service_tickets_bp.route('/<int:service_ticket_id>', methods=['PUT'])
@limiter.limit("20 per hour", override_defaults=True)
def update_service_ticket(service_ticket_id):
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
    print(f"Service Ticket updated: for customer {service_ticket.customer_id}")
    return service_ticket_schema.jsonify(service_ticket), 200

# ==========================================================================

@service_tickets_bp.route('/popular', methods=['GET'])
@limiter.limit("10 per hour")
@cache.cached(timeout=30)   
def popular_service_tickets():
    
    popular_tickets = db.session.query(Service_Ticket).all()
    
    popular_tickets.sort(key=lambda ticket: ticket.complete_count, reverse=True)
    
    ticket_data = [
        {
            "id": ticket.id,
            "service_description": ticket.service_description,
            "price": ticket.price,
        }
        for ticket in popular_tickets
    ]
    
    return jsonify(ticket_data[:3]), 200

# ==========================================================================

# @service_tickets_bp.route('/<int:mechanic_id>/mechanics', methods=['GET'])
# def get_ticket_mechanics(mechanic_id):
#     ticket = db.session.get(Service_Ticket, mechanic_id)
#     if not ticket:
#         return jsonify({"message": "Ticket not found"}), 404

#     mechanics_list = [
#         {"id": m.id, "first_name": m.first_name, "last_name": m.last_name, "email": m.email}
#         for m in ticket.mechanics
#     ]
#     return jsonify(mechanics_list), 200

# # ==========================================================================

# @service_tickets_bp.route('/<int:ticket_id>/assign_mechanics', methods=['POST'])
# def assign_mechanics(ticket_id):
#     ticket = db.session.get(Service_Ticket, ticket_id)
#     if not ticket:
#         return jsonify({"message": "Ticket not found"}), 404

#     mechanic_ids = request.json.get("mechanic_ids", [])
#     if not mechanic_ids:
#         return jsonify({"message": "No mechanics provided"}), 400

#     for mech_id in mechanic_ids:
#         mechanic = db.session.get(Mechanics, mech_id)
#         if mechanic and mechanic not in ticket.mechanics:
#             ticket.mechanics.append(mechanic)

#     db.session.commit()
#     return service_ticket_schema.jsonify(ticket), 200