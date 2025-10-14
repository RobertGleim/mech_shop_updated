from . import mechanics_bp
from .schema import mechanic_schema, mechanics_schema, login_schema
from flask import request, jsonify, current_app
import traceback
from marshmallow import ValidationError
from app.models import Mechanics, db
from app.extenstions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import role_required, token_required, create_admin_token, create_mechanic_token

# Blueprint-level exception handler so blueprint errors always return JSON
@mechanics_bp.errorhandler(Exception)
def mechanics_blueprint_error(err):
    # Log the exception with traceback
    current_app.logger.exception("Unhandled exception in mechanics blueprint")
    tb = traceback.format_exc()
    payload = {"message": "Internal server error", "error": str(err)}
    # include traceback when app.debug is True
    if current_app.debug:
        payload["traceback"] = tb
    resp = jsonify(payload)
    resp.status_code = 500
    return resp

#  =========================================================================

@mechanics_bp.route("/login", methods=["POST"])
def login_mechanics():
    try:
        # Safely get JSON body (silent=True avoids raising on malformed JSON)
        payload = request.get_json(silent=True) or {}
        # If schema expects specific fields, validate the payload via the schema
        try:
            data = login_schema.load(payload)
        except ValidationError:
            data = payload or {}

        # Mask password when logging
        try:
            current_app.logger.debug("Login attempt payload (masked): %s", {k: (v if k != 'password' else '***') for k, v in data.items()})
        except Exception:
            pass

        identifier = (data.get('email') or data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        if not identifier or not password:
            return jsonify({"message": "Email/username and password are required."}), 400

        # Use filter() for clarity and portability
        mechanics = db.session.query(Mechanics).filter(Mechanics.email == identifier).first()

        if mechanics and check_password_hash(mechanics.password, password):
            is_admin_flag = bool(getattr(mechanics, "is_admin", False))
            token = create_admin_token(mechanics.id) if is_admin_flag else create_mechanic_token(mechanics.id)

            return jsonify({
                "message": f"Login successful {mechanics.first_name} {mechanics.last_name}",
                "token": token,
                "id": mechanics.id,
                "is_admin": is_admin_flag
            }), 200

        return jsonify({"message": "Invalid email or password"}), 403

    except Exception as exc:
        current_app.logger.exception("Unhandled error in login_mechanics")
        tb = traceback.format_exc()
        payload = {"message": "Internal server error", "error": str(exc)}
        if current_app.debug:
            payload["traceback"] = tb
        return jsonify(payload), 500

#  =========================================================================

@mechanics_bp.route('/', methods=['POST'])
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

@mechanics_bp.route('/', methods=['GET'])
@cache.cached(timeout=30)
@role_required(['admin'])
@token_required
def get_mechanics(user_id, role):
    mechanics = db.session.query(Mechanics).all()
    return mechanics_schema.jsonify(mechanics), 200

#  =========================================================================

@mechanics_bp.route('/profile', methods=['GET'])
@cache.cached(timeout=30)
@role_required(['admin', 'mechanic'])
@token_required
def get_mechanic(user_id, role):
    mechanic = db.session.get(Mechanics, user_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    print(f"Mechanic found: {mechanic.first_name} {mechanic.last_name}")
    return mechanic_schema.jsonify(mechanic), 200

#  =========================================================================

@mechanics_bp.route('/<int:mech_id>', methods=['GET'])
@role_required(['admin', 'mechanic'])
@token_required
def get_mechanic_by_id(user_id, role, mech_id):
    # allow admin or the user themself
    if role != 'admin' and int(user_id) != int(mech_id):
        return jsonify({"message": "You do not have permission to view this mechanic."}), 403
    mechanic = db.session.get(Mechanics, mech_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    return mechanic_schema.jsonify(mechanic), 200

#  =========================================================================

@mechanics_bp.route('/<int:mech_id>', methods=['PUT'])
@role_required(['admin', 'mechanic'])
@token_required
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

@mechanics_bp.route('/<int:mech_id>', methods=['DELETE'])
@role_required(['admin'])
@token_required
def delete_mechanic_by_id(user_id, role, mech_id):
    mechanic = db.session.get(Mechanics, mech_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    db.session.delete(mechanic)
    db.session.commit()
    print(f"Mechanic deleted: {mechanic.first_name} {mechanic.last_name}")
    return jsonify({"message": f"Mechanic {mech_id} deleted"}), 200

#  =========================================================================

@mechanics_bp.route('/', methods=['PUT'], strict_slashes=False)
@role_required(['admin'])
@token_required
def update_all_mechanics(user_id, role):
    return jsonify({"message": "Bulk update not supported"}), 400

@mechanics_bp.route('/', methods=['DELETE'], strict_slashes=False)
@role_required(['admin'])
@token_required
def delete_all_mechanics(user_id, role):
    mechanics = db.session.query(Mechanics).all()
    for mechanic in mechanics:
        db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": "All mechanics deleted"}), 200
