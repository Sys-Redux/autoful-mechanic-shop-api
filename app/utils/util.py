from datetime import datetime, timedelta, timezone
from jose import jwt
from functools import wraps
from flask import request, jsonify
import os
import jose
from app.utils.firebase_admin import verify_firebase_token
from app.models import Customer, Mechanic

SECRET_KEY = os.environ.get('SECRET_KEY') or 'ThisIsASuperSecretKeyToProtextTheGoods'

# ========== LEGACY JWT TOKEN FUNCTIONS ==========
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

# ========== FIREBASE TOKEN DECORATORS ==========
"""
Key improvement:
    Lookup db_id instead of firebase_uid enables fast primary key lookups
    $O(1)$ complexity
"""
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

        decoded = verify_firebase_token(token)
        if not decoded:
            return jsonify({'message': 'Token is invalid!'}), 401

        # Attach Firebase user info to request (includes claims)
        request.firebase_user = decoded
        request.firebase_uid = decoded.get('uid')
        request.user_role = decoded.get('role')
        request.user_db_id = decoded.get('db_id')

        return f(*args, **kwargs)
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

        decoded = verify_firebase_token(token)
        if not decoded:
            return jsonify({'message': 'Token is invalid!'}), 401

        # Check role from custom claims
        role = decoded.get('role')
        db_id = decoded.get('db_id')

        if role != 'customer':
            return jsonify({'message': 'Customer authorization required'}), 403
        if not db_id:
            return jsonify({'message': 'User not properly registered'}), 403

        customer = Customer.query.get(db_id)
        if not customer:
            return jsonify({'message': 'Customer not found'}), 404

        request.firebase_user = decoded
        request.current_customer = customer

        return f(*args, **kwargs)
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

        decoded = verify_firebase_token(token)
        if not decoded:
            return jsonify({'message': 'Token is invalid!'}), 401

        role = decoded.get('role')
        db_id = decoded.get('db_id')

        if role != 'mechanic':
            return jsonify({'message': 'Mechanic authorization required'}), 403
        if not db_id:
            return jsonify({'message': 'User not properly registered'}), 403

        mechanic = Mechanic.query.get(db_id)
        if not mechanic:
            return jsonify({'message': 'Mechanic not found'}), 404

        request.firebase_user = decoded
        request.current_mechanic = mechanic

        return f(*args, **kwargs)
    return decorated