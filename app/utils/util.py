from datetime import datetime, timedelta, timezone
from jose import jwt
from functools import wraps
from flask import request, jsonify
import jose

SECRET_KEY = "ThisIsASuperSecretKeyToProtectTheJWT"

def encode_token(user_id, role='customer'):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0,hours=1),
        'iat': datetime.now(timezone.utc),
        'sub': str(user_id),
        'role': role
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def encode_customer_token(customer_id):
    return encode_token(customer_id, role='customer')

def encode_mechanic_token(mechanic_id):
    return encode_token(mechanic_id, role='mechanic')

def token_required(f):
    """General Token - Accepts Any Valid Token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data['sub']
            role = data.get('role', 'customer') # Default to customer

        except jose.JWTError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except jose.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401

        return f(user_id, *args, **kwargs)
    return decorated

def customer_token_required(f):
    """Customer Token - Only Accepts Customer Tokens"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data['sub']
            role = data.get('role')

            if role != 'customer':
                return jsonify({'message': 'Customer authorization required'}), 403

        except jose.JWTError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except jose.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401

        return f(user_id, *args, **kwargs)
    return decorated

def mechanic_token_required(f):
    """Mechanic Token - Only Accepts Mechanic Token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data['sub']
            role = data.get('role')

            if role != 'mechanic':
                return jsonify({'message': 'Mechanic authorization required'}), 403

        except jose.JWTError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except jose.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401

        return f(user_id, *args, **kwargs)
    return decorated