from . import customers_bp
from .schema import customer_schema, customers_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, db
from app.extenstions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import role_required, token_required, create_customer_token

#  =========================================================================

@customers_bp.route("/login", methods=["POST"])
def login_customer():
    try:
        data = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    customer = db.session.query(Customers).where(Customers.email == data["email"]).first()

    if customer and check_password_hash(customer.password, data["password"]):
        token = create_customer_token(customer.id)
        return jsonify({
            "message": f"Login successful {customer.first_name} {customer.last_name}",
            "token": token
        }), 200
    return jsonify({"message": "Invalid email or password"}), 403

#  =========================================================================

@customers_bp.route('/', methods=['POST'])
def create_customer():
    try:
        data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    existing_customer = db.session.query(Customers).filter_by(email=data['email']).first()
    if existing_customer:
        return jsonify({"message": "Email already in use"}), 409

    data['password'] = generate_password_hash(data['password'])
    new_customer = Customers(**data)
    db.session.add(new_customer)
    db.session.commit()
    print(f"New customer was created, Hello: {new_customer.first_name} {new_customer.last_name}")
    return customer_schema.jsonify(new_customer), 201

#  =========================================================================

@customers_bp.route('/', methods=['GET'])
@cache.cached(timeout=30)
@role_required(['admin', 'customer', 'mechanic'])
@token_required
def get_customers(user_id, role):
    customers = db.session.query(Customers).all()
    return jsonify({"customers": customers_schema.dump(customers)}), 200

#  =========================================================================

@customers_bp.route('/profile', methods=['GET'])
@cache.cached(timeout=30)
@role_required(['admin', 'customer'])
@token_required
def get_customer(user_id, role):
    customer = db.session.get(Customers, user_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    print(f"Customer found: {customer.first_name} {customer.last_name}")
    return customer_schema.jsonify(customer), 200

#  =========================================================================

@customers_bp.route('/<int:customer_id>', methods=['GET'])
@role_required(['admin', 'customer'])
@token_required
def get_customer_by_id(user_id, role, customer_id):
    # allow admin or the user themself
    if role != 'admin' and int(user_id) != int(customer_id):
        return jsonify({"message": "You do not have permission to view this customer."}), 403
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    return customer_schema.jsonify(customer), 200

#  =========================================================================

@customers_bp.route('/', methods=['PUT'], strict_slashes=False)
@role_required(['admin', 'customer'])
@token_required
def update_customer_without_id(user_id, role):
    # For customers, update their own profile using the token user_id
    customer = db.session.get(Customers, user_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"message": e.messages}), 400

    # Hash password if present
    if 'password' in customer_data and customer_data['password']:
        customer_data['password'] = generate_password_hash(customer_data['password'])

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    print(f"Customer updated: {customer.first_name} {customer.last_name}")
    return customer_schema.jsonify(customer), 200

@customers_bp.route('/<int:customer_id>', methods=['PUT'], strict_slashes=False)
@role_required(['admin', 'customer'])
@token_required
def update_customer_by_id(user_id, role, customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    # Only allow non-admins to update their own record
    if role != 'admin' and int(user_id) != int(customer_id):
        return jsonify({"message": "You do not have permission to update this customer."}), 403

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"message": e.messages}), 400

    # Hash password if present
    if 'password' in customer_data and customer_data['password']:
        customer_data['password'] = generate_password_hash(customer_data['password'])

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    print(f"Customer updated: {customer.first_name} {customer.last_name}")
    return customer_schema.jsonify(customer), 200

#  =========================================================================

@customers_bp.route('/', methods=['DELETE'], strict_slashes=False)
@role_required(['admin'])
@token_required
def delete_all_customers(user_id, role):
    customers = db.session.query(Customers).all()
    for customer in customers:
        db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "All customers deleted"}), 200

@customers_bp.route('/<int:customer_id>', methods=['DELETE'], strict_slashes=False)
@role_required(['admin'])
@token_required
def delete_customer_by_id(user_id, role, customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    # Prevent admin from deleting themselves
    if int(user_id) == int(customer_id):
        return jsonify({"message": "Cannot delete your own account"}), 403

    db.session.delete(customer)
    db.session.commit()
    print(f"Customer deleted: {customer.first_name} {customer.last_name}")
    return jsonify({"message": f"Customer {customer_id} deleted"}), 200
