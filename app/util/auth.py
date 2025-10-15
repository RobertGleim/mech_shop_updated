from jose import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from jose import exceptions as jose_exceptions
import os

SECRET_KEY = os.environ.get("SECRET_KEY") or "super secret key"


def create_admin_token(user_id):
    return encode_token(user_id, role='admin')

def create_mechanic_token(user_id):
    return encode_token(user_id, role='mechanic')

def create_customer_token(user_id):
    return encode_token(user_id, role='customer')


def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # role is expected to be injected by token_required into kwargs
            role = kwargs.get('role')
            if role not in required_roles:
                return jsonify({'message': 'You do not have permission to access this resource.'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def encode_token(user_id, role='mechanic'):
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "sub": str(user_id),
        "role": role  # <-- role is set here
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"DEBUG: token_required called for endpoint: {request.path}")
        token = None
        auth_header = request.headers.get('Authorization')
        print(f"DEBUG: Authorization header: {auth_header}")  # <--- Add this line
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        if not token:
            token = request.cookies.get('token')
            print(f"DEBUG: Cookie token: {token}")  # <--- Add this line
        if not token:
            token = request.args.get('token')
            print(f"DEBUG: Query param token: {token}")  # <--- Add this line
        if not token:
            print("DEBUG: No token found in request headers/cookies/query params")
            return jsonify({'message': 'Token is missing!'}), 401 
        try:
            print(f"DEBUG: Decoding token: {token[:20]}...")
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = data.get("sub")
            role = data.get("role", "mechanic")
        except jose_exceptions.ExpiredSignatureError:
            print("DEBUG: Token expired")
            return jsonify({"message": "Token is expired!"}), 401
        except jose_exceptions.JWTError as e:
            print(f"DEBUG: Token invalid: {e}")
            return jsonify({"message": "Token is invalid!"}), 401
        kwargs = dict(kwargs)
        kwargs['user_id'] = user_id
        kwargs['role'] = role
        return f(*args, **kwargs)
    return decorated