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
        "role": role
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 1) Try Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()

        # 2) Fallback to cookie (if using cookie-based storage)
        if not token:
            token = request.cookies.get('token')

        # 3) Fallback to query parameter ?token=...
        if not token:
            token = request.args.get('token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401 

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = data.get("sub")
            role = data.get("role", "mechanic")
        except jose_exceptions.ExpiredSignatureError:
            return jsonify({"message": "Token is expired!"}), 401
        except jose_exceptions.JWTError:
            return jsonify({"message": "Token is invalid!"}), 401

        # Inject user_id and role into kwargs safely, then call the wrapped function
        kwargs = dict(kwargs)  # copy to avoid mutating caller's dict
        kwargs['user_id'] = user_id
        kwargs['role'] = role

        return f(*args, **kwargs)
    return decorated