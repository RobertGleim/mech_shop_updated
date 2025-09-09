from select import select
from app.blueprints import customers
from app.util.auth import role_required, token_required
from . import ticket_mechanics_bp
from .schema import ticket_mechanic_schema, ticket_mechanics_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, Ticket_Mechanics, Service_Ticket, Mechanics, db
from app.extenstions import limiter, cache
from sqlalchemy import func

 #  =========================================================================
 
@ticket_mechanics_bp.route('/', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
@token_required
@role_required(['admin'])
def create_ticket_mechanic(user_id, role):
    try:
        data = ticket_mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_ticket_mechanic = Ticket_Mechanics(**data)
    db.session.add(new_ticket_mechanic)
    db.session.commit()
    print(f"New Ticket was created:  ")
    return ticket_mechanic_schema.jsonify(new_ticket_mechanic), 201

 #  =========================================================================

@ticket_mechanics_bp.route('/', methods=['GET'])
@limiter.limit("50 per hour", override_defaults=True)
@cache.cached(timeout=20)
@token_required
@role_required(['admin'])
def get_ticket_mechanics(user_id, role):
    ticket_mechanics = db.session.query(Ticket_Mechanics).all()
    return ticket_mechanics_schema.jsonify(ticket_mechanics), 200

 #  =========================================================================

@ticket_mechanics_bp.route('/<int:service_ticket_id>/get_ticket_mechanic', methods=['GET'])
@limiter.limit("50 per hour", override_defaults=True)
@token_required
@role_required(['admin'])
def get_ticket_mechanic(service_ticket_id, role, user_id):
    ticket_mechanics = db.session.query(Ticket_Mechanics).filter_by(service_ticket_id=service_ticket_id).all()
 
    if not ticket_mechanics:
        return jsonify({"message": "ticket_mechanic not found"}), 404
    
    return ticket_mechanics_schema.jsonify(ticket_mechanics), 200

 #  =========================================================================

@ticket_mechanics_bp.route('/<int:service_ticket_id>/<int:mechanic_id>', methods=['DELETE']) 
@limiter.limit("3 per hour") 
@token_required
@role_required(['admin'])
def delete_ticket_mechanic(user_id, role, service_ticket_id, mechanic_id):
    ticket_mechanic = db.session.get(Ticket_Mechanics, (service_ticket_id, mechanic_id))
    if not ticket_mechanic:
        return jsonify({"message": "ticket_mechanic not found"}), 404
    db.session.delete(ticket_mechanic)
    db.session.commit()
    return jsonify({"message": f"Ticket was deleted: ({service_ticket_id}, {mechanic_id})"}), 200
 #  =========================================================================

@ticket_mechanics_bp.route('/<int:service_ticket>/<int:mechanic_id>', methods=['PUT'])
@limiter.limit("20 per hour", override_defaults=True)
@token_required
@role_required(['admin'])
def update_ticket_mechanic(user_id, role, service_ticket, mechanic_id):
    ticket_mechanic = (db.session.query(Ticket_Mechanics).filter_by(service_ticket_id=service_ticket, mechanic_id=mechanic_id).first())
    
    if not ticket_mechanic:
        return jsonify({"message": "ticket not found"}), 404
    try:
        ticket_mechanic_data = ticket_mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"Message": e.messages}), 400
    for key, value in ticket_mechanic_data.items():
        if key in ['service_ticket_id', 'mechanic_id']:
            continue
        setattr(ticket_mechanic, key, value)
    db.session.commit()
    print(f"ticket updated: ({service_ticket}, {mechanic_id})")
    return ticket_mechanic_schema.jsonify(ticket_mechanic), 200

# ======================================================================

@ticket_mechanics_bp.route('/<int:ticket_id>/assign_mechanics', methods=['POST'])
@token_required
@role_required(['admin'])
def assign_mechanics(user_id, role,ticket_id):
    ticket = db.session.get(Service_Ticket, ticket_id)
    if not ticket:
        return jsonify({"message": "Ticket not found"}), 404
    mechanic_ids = request.json.get("mechanic_ids", [])
    if not mechanic_ids:
        return jsonify({"message": "No mechanics provided"}), 400

    for mech_id in mechanic_ids:
        mechanic = db.session.get(Mechanics, mech_id)
        if mechanic and mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)
    print(f"Mechanics assigned to ticket {ticket_id}: {mechanic_ids}")
    db.session.commit()
    return ticket_mechanic_schema.jsonify(ticket), 200

#==========================================================================

@ticket_mechanics_bp.route('/<int:ticket_id>/unassign_mechanics', methods=['DELETE'])
@token_required
@role_required(['admin'])
def unassign_mechanics(user_id, role, ticket_id):
    ticket = db.session.get(Service_Ticket, ticket_id)
    if not ticket:
        return jsonify({"message": "Ticket not found"}), 404

    mechanic_ids = request.json.get("mechanic_ids", [])
    if not mechanic_ids:
        return jsonify({"message": "No mechanics provided"}), 400

    for mech_id in mechanic_ids:
        mechanic = db.session.get(Mechanics, mech_id)
        if mechanic and mechanic in ticket.mechanics:
            ticket.mechanics.remove(mechanic)
    print(f"Mechanics unassigned from ticket {ticket_id}: {mechanic_ids}")
    db.session.commit()
    return ticket_mechanic_schema.jsonify(ticket), 200


# ==========================================================================

@ticket_mechanics_bp.route('/<int:mechanic_id>/get_mechanic', methods=['GET'])
@token_required
@role_required(['admin'])
@cache.cached(timeout=30)
def get_mechanics(mechanic_id, user_id, role):
    tickets = (
    db.session.query(Service_Ticket).join(Ticket_Mechanics).filter(Ticket_Mechanics.mechanic_id == mechanic_id)
    .all())
    if not tickets:
        return jsonify({"message": "Ticket not found"}), 404

    tickets_list = [
        {
            "ticket_id": ticket.id, 
            "service_description": ticket.service_description,
            "price": ticket.price,
            "vin": ticket.vin,
            "service_date": ticket.service_date.isoformat(),
            "mechanics": [
                {
                    "id": m.id,
                    "first_name": m.first_name,
                    "last_name": m.last_name,
                    "email": m.email
                }
                for m in ticket.mechanics
            ]
        }
        for ticket in tickets
    ]
    print(tickets_list) 
    
    return jsonify(tickets_list), 200

# ==========================================================================

@ticket_mechanics_bp.route('/get_ticket_customer', methods=['GET'])
@token_required
@role_required(['admin'])
@cache.cached(timeout=30)
def get_ticket_customers(user_id, role):
    
    customer = db.session.get(Customers, user_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
     
    tickets = db.session.query(Service_Ticket).filter_by(customer_id=user_id).all()

    customer_info = {
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone": customer.phone  
    }

    tickets_list = [
        {
            "ticket_id": ticket.id,
            "service_description": ticket.service_description,
            "price": ticket.price,
            "vin": ticket.vin,
            "service_date": ticket.service_date.isoformat()
        }
        for ticket in tickets
    ]

    return jsonify({"customer": customer_info,"tickets": tickets_list}), 200

#=========================================================================
@ticket_mechanics_bp.route('/get_most_ticket_mechanic', methods=['GET'])
@limiter.limit("50 per hour", override_defaults=True)
@cache.cached(timeout=20) 
@token_required
@role_required(['admin'])  
def get_most_ticket_mechanics(user_id, role):
    if role != 'admin':
        return jsonify({"message": "Unauthorized"}), 403

    top_mechanics = (
        db.session.query(
            Mechanics.id,
            Mechanics.first_name,
            Mechanics.last_name,
            Mechanics.email,
            func.count(Service_Ticket.id).label('ticket_count')
        )
        .join(Service_Ticket.mechanics)  
        .group_by(Mechanics.id)
        .order_by(func.count(Service_Ticket.id).desc())
        .limit(3)
        .all()
    )

    # Prepare response
    mechanics_list = [
        {
            "id": m.id,
            "first_name": m.first_name,
            "last_name": m.last_name,
            "email": m.email,
            "ticket_count": m.ticket_count
        }
        for m in top_mechanics
    ]

    return jsonify(mechanics_list), 200
   
 
