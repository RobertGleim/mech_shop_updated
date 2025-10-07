from . import customers_bp
from .schema import customer_schema, customers_schema,login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, db
from app.extenstions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import role_required, token_required, encode_token

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
 
@customers_bp.route('', methods=['GET'])
# limiter left blank to use default limits
@token_required
@role_required(['admin', 'mechanic'])
def get_customers(user_id, role):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 2, type=int)
    
    paginated_customers = db.session.query(Customers).paginate(page=page, per_page=per_page,)
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

 #  =========================================================================
 
@customers_bp.route('/profile', methods=['GET'])
# limiter left blank to use default limits
@token_required
@role_required(['admin', 'mechanic', 'customer'])
def get_customer(user_id,role):
    
    customer = db.session.get(Customers, user_id) 
    print(f"Customer found: {user_id} ")
    return customer_schema.jsonify(customer), 200

 #  =========================================================================
 
@customers_bp.route('', methods=['DELETE'])
@limiter.limit("3 per hour") 
@token_required
@role_required(['admin'])
def delete_customer(user_id, role):
    
    customer = db.session.get(Customers,user_id)
    db.session.delete(customer)
    db.session.commit()
    print(f"Customer deleted: {customer.first_name} {customer.last_name}")
    return jsonify({"message": f"Sorry to see you go! {user_id}"}), 200

 #  =========================================================================
 
@customers_bp.route('', methods=['PUT', 'PATCH'])
@limiter.limit("20 per hour", override_defaults=True)
@token_required
@role_required(['admin', 'mechanic', 'customer'])
def update_customer(user_id, role):
    
    customer = db.session.get(Customers, user_id)
    
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
