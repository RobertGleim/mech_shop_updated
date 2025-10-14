from . import customers_bp
from .schema import customer_schema, customers_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, db
from app.extenstions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import role_required, token_required, create_customer_token
from sqlalchemy import or_

#=========================================================================

@customers_bp.route("/login", methods=["POST"])
def login_customer():
    try:
        data = login_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages), 400
    
    customer = db.session.query(Customers).where(Customers.email==data["email"]).first()
    
    if customer and check_password_hash(customer.password, data["password"]):
        token = create_customer_token(customer.id)
        return jsonify({
            "message": f"Login successful {customer.first_name} {customer.last_name}",
            "token": token
        }), 200
    return jsonify({"message": "Invalid email or password"}), 403 
  
#=========================================================================

@customers_bp.route('', methods=['POST'])
def create_customer():
    try:
        data = customer_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages), 400
    data['password'] = generate_password_hash(data['password'])

    new_customer = Customers(**data)
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

#=========================================================================
 
@customers_bp.route('', methods=['GET'])
@token_required
@role_required(['admin', 'mechanic'])
def get_customers(user_id, role):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    q = request.args.get('q', None, type=str)

    query = db.session.query(Customers)
    if q:
        like_term = f"%{q}%"
        query = query.filter(
            or_(
                Customers.first_name.ilike(like_term),
                Customers.last_name.ilike(like_term),
                Customers.email.ilike(like_term)
            )
        )

    paginated_customers = query.paginate(page=page, per_page=per_page)
    result = customers_schema.dump(paginated_customers.items)

    response = {
        "customers": result,
        "total": paginated_customers.total,
        "page": paginated_customers.page,
        "pages": paginated_customers.pages,
        "per_page": paginated_customers.per_page,
        "has_next": paginated_customers.has_next,
        "has_prev": paginated_customers.has_prev
    }

    return jsonify(response), 200

#=========================================================================
 
@customers_bp.route('/profile', methods=['GET'])
@token_required
@role_required(['admin', 'mechanic', 'customer'])
def get_customer(user_id, role):
    customer = db.session.get(Customers, user_id) 
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    return customer_schema.jsonify(customer), 200

#=========================================================================
 
@customers_bp.route('', methods=['DELETE'])
@token_required
@role_required(['admin', 'mechanic', 'customer'])
def delete_customer(user_id, role):
    # Prevent admin users from deleting themselves via this endpoint
    if role == 'admin':
        return jsonify({"message": "Admin users are not allowed to delete their own account here."}), 403

    customer = db.session.get(Customers, user_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    try:
        db.session.delete(customer)
        db.session.commit()
        return ('', 204)
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Failed to delete customer"}), 500

#=========================================================================
 
@customers_bp.route('', methods=['PUT', 'PATCH'])
@token_required
@role_required(['admin', 'mechanic', 'customer'])
def update_customer(user_id, role):
    customer = db.session.get(Customers, user_id)
    
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    try:
        # Use partial=True to allow partial updates without requiring all fields
        customer_data = customer_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify({"message": e.messages}), 400
    
    # Only hash password if it's being updated
    if 'password' in customer_data:
        customer_data['password'] = generate_password_hash(customer_data['password'])
    
    for key, value in customer_data.items():
        setattr(customer, key, value)
    db.session.commit()
    return customer_schema.jsonify(customer), 200


@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_customer_by_id(user_id, role, customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": f"Customer {customer_id} deleted"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Failed to delete customer"}), 500


@customers_bp.route('/<int:customer_id>', methods=['PUT', 'PATCH'])
@token_required
@role_required(['admin'])
def update_customer_by_id(user_id, role, customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    try:
        # allow partial updates
        data = customer_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    if 'password' in data:
        data['password'] = generate_password_hash(data['password'])
    try:
        for key, value in data.items():
            setattr(customer, key, value)
        db.session.commit()
        return customer_schema.jsonify(customer), 200
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Failed to update customer"}), 500