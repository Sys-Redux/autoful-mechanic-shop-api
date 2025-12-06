from datetime import datetime, timedelta, timezone
from jose import jwt
from functools import wraps
from flask import request, jsonify
import os
import jose
from app.models import Customer, Mechanic, db

SECRET_KEY = os.environ.get('SECRET_KEY') or 'ThisIsASuperSecretKeyToProtextTheGoods'


# ========== LEGACY JWT TOKEN FUNCTIONS ==========

def encode_token(user_id, role='customer'):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0, hours=1),
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


def decode_legacy_token(token: str) -> dict | None:
    """
    Decode a legacy JWT token (python-jose).
    Returns decoded payload or None if invalid.
    """
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return {
            'uid': None,  # Legacy tokens don't have Firebase UID
            'db_id': int(data['sub']),
            'role': data.get('role', 'customer')
        }
    except jose.JWTError:
        return None
    except jose.ExpiredSignatureError:
        return None


def verify_token(token: str) -> dict | None:
    """
    Verify a token - tries Firebase first, then falls back to legacy JWT.

    Returns:
        dict with 'uid', 'db_id', 'role' or None if invalid
    """
    # Try Firebase token first
    try:
        from app.utils.firebase_admin import verify_firebase_token
        decoded = verify_firebase_token(token)
        if decoded:
            return {
                'uid': decoded.get('uid'),
                'db_id': decoded.get('db_id'),
                'role': decoded.get('role'),
                'firebase_user': decoded
            }
    except Exception:
        # Firebase not initialized or token invalid - try legacy
        pass

    # Fall back to legacy JWT
    return decode_legacy_token(token)


# ========== HYBRID TOKEN DECORATORS ==========

def token_required(f):
    """General Token - Accepts Firebase or Legacy JWT Token"""
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

        decoded = verify_token(token)
        if not decoded:
            return jsonify({'message': 'Token is invalid!'}), 401

        # Attach user info to request
        request.firebase_user = decoded.get('firebase_user')
        request.firebase_uid = decoded.get('uid')
        request.user_role = decoded.get('role')
        request.user_db_id = decoded.get('db_id')

        return f(*args, **kwargs)
    return decorated


def customer_token_required(f):
    """Customer Token - Requires authentication as a customer"""
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

        decoded = verify_token(token)
        if not decoded:
            return jsonify({'message': 'Token is invalid!'}), 401

        # Check role
        role = decoded.get('role')
        db_id = decoded.get('db_id')

        if role != 'customer':
            return jsonify({'message': 'Customer authorization required'}), 403
        if not db_id:
            return jsonify({'message': 'User not properly registered'}), 403

        customer = db.session.get(Customer, db_id)
        if not customer:
            return jsonify({'message': 'Customer not found'}), 404

        request.firebase_user = decoded.get('firebase_user')
        request.current_customer = customer

        return f(*args, **kwargs)
    return decorated


def mechanic_token_required(f):
    """Mechanic Token - Requires authentication as a mechanic"""
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

        decoded = verify_token(token)
        if not decoded:
            return jsonify({'message': 'Token is invalid!'}), 401

        role = decoded.get('role')
        db_id = decoded.get('db_id')

        if role != 'mechanic':
            return jsonify({'message': 'Mechanic authorization required'}), 403
        if not db_id:
            return jsonify({'message': 'User not properly registered'}), 403

        mechanic = db.session.get(Mechanic, db_id)
        if not mechanic:
            return jsonify({'message': 'Mechanic not found'}), 404

        request.firebase_user = decoded.get('firebase_user')
        request.current_mechanic = mechanic

        return f(*args, **kwargs)
    return decorated