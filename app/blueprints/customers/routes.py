from app.utils.util import token_required
from .schemas import customer_schema, customers_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Customer, db
from app.extensions import limiter, cache
from app.utils.util import encode_token
from . import customers_bp


# Login Customer
@customers_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login_customer():
    try:
        credentials = request.json
        email = credentials['email']
        password = credentials['password']
    except KeyError:
        return jsonify({"message": "Email and password are required."}), 400

    query = select(Customer).where(Customer.email == email)
    customer = db.session.execute(query).scalar_one_or_none()

    if customer and customer.password == password:
        auth_token = encode_token(customer.id)

        response = {
            'status': 'success',
            'message': 'Login successful',
            'auth_token': auth_token
        }
        return jsonify(response), 200
    return jsonify({"message": "Invalid email or password."}), 401


# Create A Customer
@customers_bp.route('/', methods=['POST'])
@limiter.limit("5 per hour")
def create_customer():
    try:
        new_customer = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    query = select(Customer).where(Customer.email == new_customer.email)
    existing_customer = db.session.execute(query).scalars().all()
    if existing_customer:
        return jsonify({"message": "Customer with this email already exists."}), 400
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

# Get All Customers
@customers_bp.route('/', methods=['GET'])
@cache.cached(timeout=60)
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()
    return customers_schema.jsonify(customers), 200

# Get a Specific Customer
@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer:
        return customer_schema.jsonify(customer), 200
    return jsonify({"message": "Customer not found."}), 404

# Update Customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    try:
        customer_schema.load(request.json, instance=customer, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()
    return customer_schema.jsonify(customer), 200

# Delete Customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@limiter.limit("5 per hour")
@token_required
def delete_customer(user_id, customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'}), 200
