from select import select
from app.blueprints import customers
from app.util.auth import token_required
from . import ticket_mechanics_bp
from .schema import ticket_mechanic_schema, ticket_mechanics_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, Ticket_Mechanics, Service_Ticket, Mechanics, db
from app.extenstions import limiter, cache

 #  =========================================================================
 
@ticket_mechanics_bp.route('/', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
def create_ticket_mechanic():
    try:
        data = ticket_mechanic_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400

    new_ticket_mechanic = Ticket_Mechanics(**data)
    db.session.add(new_ticket_mechanic)
    db.session.commit()
    print(f"New Ticket was created:  ")
    return ticket_mechanic_schema.jsonify(new_ticket_mechanic), 201

 #  =========================================================================

@ticket_mechanics_bp.route('/', methods=['GET'])
@limiter.limit("50 per hour", override_defaults=True)
@cache.cached(timeout=20)
def read_ticket_mechanics():
    ticket_mechanics = db.session.query(Ticket_Mechanics).all()
    return ticket_mechanics_schema.jsonify(ticket_mechanics), 200

 #  =========================================================================

@ticket_mechanics_bp.route('/<int:ticket_mechanic_id>', methods=['GET'])
@limiter.limit("50 per hour", override_defaults=True)
@cache.cached(timeout=20)
def read_ticket_mechanic(ticket_mechanic_id):
    ticket_mechanic = db.session.get(Ticket_Mechanics, ticket_mechanic_id) 
    print(f"ticket_mechanics found: {ticket_mechanic_id}")
    return ticket_mechanic_schema.jsonify(ticket_mechanic), 200

 #  =========================================================================

@ticket_mechanics_bp.route('/<int:ticket_mechanics_id>', methods=['DELETE']) 
@limiter.limit("3 per hour") 
def delete_ticket_mechanic(ticket_mechanic_id):
    ticket_mechanic = db.session.get(Ticket_Mechanics, ticket_mechanic_id)
    db.session.delete(ticket_mechanic)
    db.session.commit()
    print(f"ticket_mechanics deleted:{ticket_mechanic_id}")
    return jsonify({"message": f"ticket was deleted: {ticket_mechanic_id}"}), 200

 #  =========================================================================

@ticket_mechanics_bp.route('/<int:ticket_mechanic_id>', methods=['PUT'])
@limiter.limit("20 per hour", override_defaults=True)
def update_ticket_mechanic(ticket_mechanic_id):
    ticket_mechanic = db.session.get(Ticket_Mechanics, ticket_mechanic_id)
    
    if not ticket_mechanic:
        return jsonify({"message": "ticket_mechanic not found"}), 404
    try:
        ticket_mechanic_data = ticket_mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"Message": e.messages}), 400
    for key, value in ticket_mechanic_data.items():
        setattr(ticket_mechanic, key, value)
    db.session.commit()
    print(f"ticket_mechanic updated: {ticket_mechanic_id}")
    return ticket_mechanic_schema.jsonify(ticket_mechanic), 200

# ======================================================================

@ticket_mechanics_bp.route('/<int:ticket_id>/assign_mechanics', methods=['POST'])
def assign_mechanics(ticket_id):
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

    db.session.commit()
    return ticket_mechanic_schema.jsonify(ticket), 200


# ==========================================================================

@ticket_mechanics_bp.route('/<int:mechanic_id>/get_ticket_mechanic', methods=['GET'])
@token_required
@cache.cached(timeout=30)
def get_ticket_mechanics(mechanic_id):
    ticket = db.session.get(Service_Ticket, mechanic_id)
    if not ticket:
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
    ]
    print(tickets_list) 
    
    return jsonify(tickets_list), 200

# ==========================================================================

@ticket_mechanics_bp.route('/<int:customers_id>/get_ticket_customer', methods=['GET'])
@token_required
@cache.cached(timeout=30)
def get_ticket_customers(customers_id):
    
    customer = db.session.get(Customers, customers_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
     
    tickets = db.session.query(Service_Ticket).filter_by(customer_id=customers_id).all()

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
   
 
