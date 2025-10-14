from . import customers_bp
from app.blueprints.mechanics.schema import mechanic_schema, mechanics_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Mechanics, db
from app.extenstions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import role_required, token_required, create_admin_token, create_mechanic_token

#  =========================================================================

@customers_bp.route("/login", methods=["POST"])
def login_mechanics():
    try:
        data = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    mechanics = db.session.query(Mechanics).where(Mechanics.email == data["email"]).first()

    if mechanics and check_password_hash(mechanics.password, data["password"]):
        # Check if mechanic is admin and generate appropriate token
        if getattr(mechanics, "is_admin", False):
            token = create_admin_token(mechanics.id)
        else:
            token = create_mechanic_token(mechanics.id)

        return jsonify({
            "message": f"Login successful {mechanics.first_name} {mechanics.last_name}",
            "token": token
        }), 200
    return jsonify({"message": "Invalid email or password"}), 403

#  =========================================================================

@customers_bp.route('/', methods=['POST'])
def create_mechanic():
    try:
        data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    existing_mechanic = db.session.query(Mechanics).filter_by(email=data['email']).first()
    if existing_mechanic:
        return jsonify({"message": "Email already in use"}), 409

    data['password'] = generate_password_hash(data['password'])
    # Ensure is_admin defaults to False if not provided
    data.setdefault('is_admin', False)
    new_mechanic = Mechanics(**data)
    db.session.add(new_mechanic)
    db.session.commit()
    print(f"New mechanic was created, Hello: {new_mechanic.first_name} {new_mechanic.last_name}")
    return mechanic_schema.jsonify(new_mechanic), 201

#  =========================================================================

@customers_bp.route('/', methods=['GET'])
@cache.cached(timeout=30)
@token_required
@role_required(['admin'])
def get_mechanics(user_id, role):
    mechanics = db.session.query(Mechanics).all()
    return mechanics_schema.jsonify(mechanics), 200

#  =========================================================================

@customers_bp.route('/profile', methods=['GET'])
@cache.cached(timeout=30)
@token_required
@role_required(['admin', 'mechanic'])
def get_mechanic(user_id, role):
    mechanic = db.session.get(Mechanics, user_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    print(f"Mechanic found: {mechanic.first_name} {mechanic.last_name}")
    return mechanic_schema.jsonify(mechanic), 200

#  =========================================================================

@customers_bp.route('/<int:mech_id>', methods=['GET'])
@token_required
@role_required(['admin', 'mechanic'])
def get_mechanic_by_id(user_id, role, mech_id):
    # allow admin or the user themself
    if role != 'admin' and int(user_id) != int(mech_id):
        return jsonify({"message": "You do not have permission to view this mechanic."}), 403
    mechanic = db.session.get(Mechanics, mech_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    return mechanic_schema.jsonify(mechanic), 200

#  =========================================================================

@customers_bp.route('/<int:mech_id>', methods=['PUT'])
@token_required
@role_required(['admin', 'mechanic'])
def update_mechanic(user_id, role, mech_id):
    mechanic = db.session.get(Mechanics, mech_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    # Only allow non-admins to update their own record
    if role != 'admin' and int(user_id) != int(mech_id):
        return jsonify({"message": "You do not have permission to update this mechanic."}), 403

    try:
        mech_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"message": e.messages}), 400

    # Hash password if present
    if 'password' in mech_data and mech_data['password']:
        mech_data['password'] = generate_password_hash(mech_data['password'])
    # Prevent downgrading admin flag by non-admins
    if role != 'admin' and 'is_admin' in mech_data:
        mech_data.pop('is_admin', None)

    for key, value in mech_data.items():
        setattr(mechanic, key, value)

    db.session.commit()
    print(f"Mechanic updated: {mechanic.first_name} {mechanic.last_name}")
    return mechanic_schema.jsonify(mechanic), 200

#  =========================================================================

@customers_bp.route('/<int:mech_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_mechanic_by_id(user_id, role, mech_id):
    mechanic = db.session.get(Mechanics, mech_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    db.session.delete(mechanic)
    db.session.commit()
    print(f"Mechanic deleted: {mechanic.first_name} {mechanic.last_name}")
    return jsonify({"message": f"Mechanic {mech_id} deleted"}), 200
