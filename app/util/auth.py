from jose import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from jose import exceptions as jose_exceptions



SECRET_KEY = "super secret key"

def encode_token(user_id, role='mechanic'):
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta( hours=1),
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
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            
        if not token:
            return jsonify({"message": "Token is missing!"}), 401 
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            print(data)
            user_id = data["sub"]
            role = data.get("role", "role")
        except jose_exceptions.ExpiredSignatureError:
            return jsonify({"message": "Token is expired!"}), 403
        except jose_exceptions.JWTError:
            return jsonify({"message": "Token is invalid!"}), 403
        return f(user_id=user_id, role=role, *args, **kwargs)
    return decorated
       
