from app.utils.util import encode_customer_token, customer_token_required
from .schemas import customer_schema, customers_schema
from app.blueprints.service_tickets.schemas import service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Customer, ServiceTicket, db
from app.extensions import limiter, cache
from bcrypt import hashpw, gensalt, checkpw
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

    if customer and checkpw(password.encode('utf-8'), customer.password.encode('utf-8')):
        auth_token = encode_customer_token(customer.id)

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
        customer_data = request.json
        if 'password' in customer_data:
            customer_data['password'] = hashpw(
                customer_data['password'].encode('utf-8'),
                gensalt()
            ).decode('utf-8')

        new_customer = customer_schema.load(customer_data)
    except ValidationError as e:
        return jsonify(e.messages), 400

    query = select(Customer).where(Customer.email == new_customer.email)
    existing_customer = db.session.execute(query).scalar_one_or_none()
    if existing_customer:
        return jsonify({"message": "Customer with this email already exists."}), 400

    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201


# Get All Customers (W/ Pagination and Caching)
@customers_bp.route('/', methods=['GET'])
@cache.cached(timeout=1)
def get_customers():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page', 10))
        query = select(Customer)
        customers = db.paginate(query, page=page, per_page=per_page)
        return customers_schema.jsonify(customers), 200
    except:
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


# Get My Service Tickets (Requires Customer Token)
@customers_bp.route('/my-tickets', methods=['GET'])
@customer_token_required
def get_my_tickets(customer_id):
    query = select(ServiceTicket).where(ServiceTicket.customer_id == customer_id)
    tickets = db.session.execute(query).scalars().all()
    return service_tickets_schema.jsonify(tickets), 200


# Update Customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@customer_token_required
def update_customer(user_id, customer_id):
    # Customer Can Only Update Their Own Account
    if int(user_id) != int(customer_id):
        return jsonify({'error': 'Unauthorized'}), 403

    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    try:
        update_data = request.json
        if 'password' in update_data:
            update_data['password'] = hashpw(
                update_data['password'].encode('utf-8'),
                gensalt()
            ).decode('utf-8')
        customer_schema.load(update_data, instance=customer, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()
    return customer_schema.jsonify(customer), 200


# Delete Customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@limiter.limit("5 per hour")
@customer_token_required
def delete_customer(user_id, customer_id):
    if int(user_id) != int(customer_id):
        return jsonify({'error': 'Unauthorized'}), 403

    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'}), 200


# List Customers With Most Tickets (Top 3)
@customers_bp.route('/top', methods=['GET'])
def get_top_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()
    customers.sort(key=lambda c: len(c.service_tickets), reverse=True)
    return customers_schema.jsonify(customers[:3]), 200