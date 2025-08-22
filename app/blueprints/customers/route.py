from . import customers_bp
from .schema import customer_schema, customers_schema,login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, db
from app.extenstions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import token_required, encode_token

 #  =========================================================================

@customers_bp.route("/login", methods=["POST"])
@limiter.limit("10 per hour")
def login_customer():
    try:
        data = login_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    
    customer = db.session.query(Customers).where(Customers.email==data["email"]).first()
    
    if customer and check_password_hash(customer.password, data["password"]):
        token = encode_token(customer.id)
        return jsonify({
            "message": f"Login successful {customer.first_name} {customer.last_name}",
            "token": token
            }), 200
    return jsonify({"message": "Invalid email or password"}), 403    
 #  =========================================================================

@customers_bp.route('/', methods=['POST'])
# @limiter.limit("3 per hour") 
def create_customer():
    try:
        data = customer_schema.load(request.json)
    except ValidationError as e: 
        return jsonify(e.messages),400
    data['password'] = generate_password_hash(data['password'])

    new_customer = Customers(**data)
    db.session.add(new_customer)
    db.session.commit()
    print(f"New Customer was created, Welcome: {new_customer.first_name} {new_customer.last_name}")
    return customer_schema.jsonify(new_customer), 201

 #  =========================================================================
 
@customers_bp.route('/', methods=['GET'])
# limiter left blank to use default limits
@token_required
def read_customers():
    customers = db.session.query(Customers).all()
    return customers_schema.jsonify(customers), 200

 #  =========================================================================
 
@customers_bp.route('/profile', methods=['GET'])
# limiter left blank to use default limits
@token_required
def read_customer():
    customer_id = request.customer_id
    customer = db.session.get(Customers, customer_id) 
    print(f"Customer found: {customer_id} ")
    return customer_schema.jsonify(customer), 200

 #  =========================================================================
 
@customers_bp.route('', methods=['DELETE'])
@limiter.limit("3 per hour") 
@token_required 
def delete_customer():
    customer_id = request.customer_id
    customer = db.session.get(Customers, customer_id)
    db.session.delete(customer)
    db.session.commit()
    print(f"Customer deleted: {customer.first_name} {customer.last_name}")
    return jsonify({"message": f"Sorry to see you go! {customer_id}"}), 200

 #  =========================================================================
 
@customers_bp.route('', methods=['PUT'])
@limiter.limit("20 per hour", override_defaults=True)
@token_required
def update_customer():
    customer_id = request.customer_id
    customer = db.session.get(Customers, customer_id)
    
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    try:
        Customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"Message": e.messages}), 400
    Customer_data['password'] = generate_password_hash(Customer_data['password'])
    for key, value in Customer_data.items():
        setattr(customer, key, value)
    db.session.commit()
    print(f"Customer updated: {customer.first_name} {customer.last_name}")
    return customer_schema.jsonify(customer), 200
