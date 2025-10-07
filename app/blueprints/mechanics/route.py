from . import mechanics_bp
from .schema import mechanic_schema, mechanics_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Mechanics, db
from app.extenstions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import role_required, token_required, encode_token

 #  =========================================================================

@mechanics_bp.route("/login", methods=["POST"])
@limiter.limit("10 per hour")
def login_mechanics():
    try:
        data = login_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    
    mechanics = db.session.query(Mechanics).where(Mechanics.email==data["email"]).first()
    
    if mechanics and check_password_hash(mechanics.password,data["password"]):
        token = encode_token(mechanics.id)
        return jsonify({
            "message": f"Login successful {mechanics.first_name} {mechanics.last_name}",
            "token": token
            }), 200
    return jsonify({"message": "Invalid email or password"}), 403   

 #  =========================================================================

@mechanics_bp.route('/', methods=['POST'])
@limiter.limit("20 per hour", override_defaults=True)
def create_mechanic():
    try:
        data = mechanic_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    
    
    existing_mechanic = db.session.query(Mechanics).filter_by(email=data['email']).first()
    if existing_mechanic:
        return jsonify({"message": "Email already in use"}), 409

    data['password'] = generate_password_hash(data['password'])
    new_mechanic = Mechanics(**data)
    db.session.add(new_mechanic)
    db.session.commit()
    print(f"New mechanic was created, Hello: {new_mechanic.first_name} {new_mechanic.last_name}")
    return mechanic_schema.jsonify(new_mechanic), 201

 #  =========================================================================

@mechanics_bp.route('', methods=['GET'])
# limiter left blank to use default limits
@cache.cached(timeout=30)
@token_required
@role_required(['admin',])
def get_mechanics(user_id, role):
    mechanics = db.session.query(Mechanics).all()
    return mechanics_schema.jsonify(mechanics), 200

 #  =========================================================================

@mechanics_bp.route('/profile', methods=['GET'])
# limiter left blank to use default limits
@cache.cached(timeout=30)
@token_required
@role_required(['admin', 'mechanic'])
def get_mechanic(user_id, role):

    mechanic = db.session.get(Mechanics, user_id)
    print(f"Mechanic found: {mechanic.first_name} {mechanic.last_name}")
    return mechanic_schema.jsonify(mechanic), 200

 #  =========================================================================

@mechanics_bp.route('', methods=['DELETE']) 
@limiter.limit("3 per hour") 
@token_required
@role_required(['admin'])
def delete_mechanic(user_id, role):
    
    mechanic = db.session.get(Mechanics, user_id)
    db.session.delete(mechanic)
    db.session.commit()
    print(f"Mechanic deleted: {mechanic.first_name} {mechanic.last_name}")
    return jsonify({"message": f"Sorry to see you go! {user_id}"}), 200

 #  =========================================================================

@mechanics_bp.route('/', methods=['PUT'])
@limiter.limit("20 per hour", override_defaults=True)
@token_required
@role_required(['admin'])
def update_mechanic(user_id, role):
    
    mechanic = db.session.get(Mechanics, user_id)
    
    if not mechanic:
        return jsonify({"message": "mechainc not found"}), 404
    try:
        Mechainc_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"Message": e.messages}), 400
    Mechainc_data['password'] = generate_password_hash(Mechainc_data['password'])
    for key, value in Mechainc_data.items():
        setattr(mechanic, key, value)
        
    db.session.commit()
    print(f"Mechanic updated: {mechanic.first_name} {mechanic.last_name}")
    return mechanic_schema.jsonify(mechanic), 200
