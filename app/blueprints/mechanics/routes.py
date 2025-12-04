from .schemas import mechanic_schema, mechanics_schema
from app.utils.util import encode_mechanic_token, mechanic_token_required
from app.utils.firebase_admin import set_user_claims
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Mechanic, db
from app.extensions import limiter, cache
from bcrypt import hashpw, gensalt, checkpw
from . import mechanics_bp


# Login Mechanic
@mechanics_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login_mechanic():
    try:
        credentials = request.json
        email = credentials['email']
        password = credentials['password']
    except KeyError:
        return jsonify({'message': 'Email and password are required.'}), 400

    query = select(Mechanic).where(Mechanic.email == email)
    mechanic = db.session.execute(query).scalar_one_or_none()

    if mechanic and checkpw(password.encode('utf-8'), mechanic.password.encode('utf-8')):
        auth_token = encode_mechanic_token(mechanic.id)

        response = {
            'status': 'success',
            'message': 'Login successful',
            'auth_token': auth_token,
            'mechanic_id': mechanic.id,
            'name': mechanic.name
        }
        return jsonify(response), 200
    return jsonify({'message': 'Invalid email or password.'}), 401


# Create A Mechanic (W/ Password Hashing)
@mechanics_bp.route('/', methods=['POST'])
@limiter.limit("5 per hour")
def create_mechanic():
    try:
        mechanic_data = request.json
        if 'password' in mechanic_data:
            mechanic_data['password'] = hashpw(
                mechanic_data['password'].encode('utf-8'),
                gensalt()
            ).decode('utf-8')

        new_mechanic = mechanic_schema.load(mechanic_data)
    except ValidationError as e:
        return jsonify(e.messages), 400

    query = select(Mechanic).where(Mechanic.email == new_mechanic.email)
    existing_mechanic = db.session.execute(query).scalars().all()
    if existing_mechanic:
        return jsonify({"message": "Mechanic with this email already exists."}), 400

    firebase_uid = mechanic_data.get('firebase_uid')
    if firebase_uid:
        existing_firebase = Mechanic.query.filter_by(firebase_uid=firebase_uid).first()
        if existing_firebase:
            return jsonify({"message": "Mechanic with this Firebase UID already exists."}), 400

    db.session.add(new_mechanic)
    db.session.commit()

    if firebase_uid:
        claims_set = set_user_claims(
            firebase_uid=firebase_uid,
            role='mechanic',
            db_id=new_mechanic.id
        )
        if not claims_set:
            print(f'Warning: Failed to set custom claims for mechanic {new_mechanic.id}')

    return mechanic_schema.jsonify(new_mechanic), 201


# Get All Mechanics (W/ Pagination and Caching)
@mechanics_bp.route('/', methods=['GET'])
@cache.cached(timeout=60)
@mechanic_token_required
def get_all_mechanics():
    try:
        page = int(request.args.get('page'))

        per_page = int(request.args.get('per_page', 10))
        query = select(Mechanic)
        mechanics = db.paginate(query, page=page, per_page=per_page)
        return mechanics_schema.jsonify(mechanics), 200
    except:
        query = select(Mechanic)
        mechanics = db.session.execute(query).scalars().all()
        return mechanics_schema.jsonify(mechanics), 200


# Get a Specific Mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['GET'])
@mechanic_token_required
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if mechanic:
        return mechanic_schema.jsonify(mechanic), 200
    return jsonify({"message": "Mechanic not found."}), 404


# Update Mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['PUT'])
@mechanic_token_required
def update_mechanic(mechanic_id):
    # Mechanics Can Only Update Their Own Account
    if request.current_mechanic.id != mechanic_id:
        return jsonify({'error': 'Unauthorized'}), 403

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    try:
        mechanic_data = request.json
        if 'password' in mechanic_data:
            mechanic_data['password'] = hashpw(
                mechanic_data['password'].encode('utf-8'),
                gensalt()
            ).decode('utf-8')

        mechanic_schema.load(mechanic_data, instance=mechanic, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200


# Delete Mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['DELETE'])
@limiter.limit("5 per hour")
@mechanic_token_required
def delete_mechanic(mechanic_id):
    # Mechanics Can Only Delete Their Own Account
    if request.current_mechanic.id != mechanic_id:
        return jsonify({'error': 'Unauthorized'}), 403

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({'message': 'Mechanic deleted successfully'}), 200


# List Mechanics With Most Tickets (Top 3)
@mechanics_bp.route('/top', methods=['GET'])
def get_top_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()
    mechanics.sort(key=lambda m: len(m.service_tickets), reverse=True)
    return mechanics_schema.jsonify(mechanics[:3]), 200