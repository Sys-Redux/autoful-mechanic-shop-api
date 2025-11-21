from .schemas import inventory_schema, inventories_schema
from app.utils.util import mechanic_token_required
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Inventory, db
from app.extensions import limiter, cache
from . import inventory_bp


# Create Inventory Part (Requires Mechanic Token)
@inventory_bp.route('/', methods=['POST'])
@mechanic_token_required
def create_inventory(user_id):
    """
    Request Body:
    {
        'part_name': 'Brake Pad',
        'price': 49.99,
        'quantity': 20
    }
    """
    try:
        new_part = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    db.session.add(new_part)
    db.session.commit()
    return inventory_schema.jsonify(new_part), 201


# Get All Inventory Parts
@inventory_bp.route('/', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def get_all_inventory():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page', 10))
        query = select(Inventory).order_by(Inventory.part_name)
        inventories = db.paginate(query, page=page, per_page=per_page)
        return inventories_schema.jsonify(inventories), 200
    except:
        query = select(Inventory).order_by(Inventory.part_name)
        inventories = db.session.execute(query).scalars().all()
        return inventories_schema.jsonify(inventories), 200


# Get Single Inventory Part
@inventory_bp.route('/<int:inventory_id>', methods=['GET'])
def get_inventory(inventory_id):
    inventory = db.session.get(Inventory, inventory_id)
    if inventory:
        return inventory_schema.jsonify(inventory), 200
    return jsonify({"message": "Inventory part not found."}), 404


# Update Inventory Part (Requires Mechanic Token)
@inventory_bp.route('/<int:inventory_id>', methods=['PUT'])
@mechanic_token_required
def update_inventory(user_id, inventory_id):
    inventory = db.session.get(Inventory, inventory_id)
    if not inventory:
        return jsonify({"message": "Inventory part not found."}), 404

    try:
        inventory_schema.load(request.json, instance=inventory, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()
    return inventory_schema.jsonify(inventory), 200


# Delete Inventory Part (Requires Mechanic Token)
@inventory_bp.route('/<int:inventory_id>', methods=['DELETE'])
@limiter.limit('10 per hour')
@mechanic_token_required
def delete_inventory(user_id, inventory_id):
    inventory = db.session.get(Inventory, inventory_id)
    if not inventory:
        return jsonify({"message": "Inventory part not found."}), 404

    # Check If Part Has Been Used in Any Service Tickets
    if inventory.service_inventories:
        return jsonify({
            'error': 'Cannot delete part that has been used on a service ticket',
            'suggestion': 'Consider setting quantity_in_stock to 0 instead'
        }), 400

    db.session.delete(inventory)
    db.session.commit()
    return jsonify({"message": "Inventory part deleted successfully."}), 200


# Search Inventory Parts by Name
@inventory_bp.route('/search', methods=['GET'])
@mechanic_token_required
def search_inventory(user_id):
    part_name = request.args.get('part_name', '')
    query = select(Inventory).where(Inventory.part_name.ilike(f'%{part_name}%'))
    inventories = db.session.execute(query).scalars().all()
    return inventories_schema.jsonify(inventories), 200


# Get Low Stock Inventory Parts (Below Threshold (Default: 5))
@inventory_bp.route('/low-stock', methods=['GET'])
@mechanic_token_required
def get_low_stock(user_id):
    threshold = int(request.args.get('threshold', 5))
    query = select(Inventory).where(Inventory.quantity_in_stock <= threshold).order_by(Inventory.quantity_in_stock)
    low_stock_parts = db.session.execute(query).scalars().all()

    return jsonify({
        'threshold': threshold,
        'count': len(low_stock_parts),
        'parts': inventories_schema.dump(low_stock_parts)
    }), 200