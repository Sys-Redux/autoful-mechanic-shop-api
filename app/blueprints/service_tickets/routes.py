from .schemas import service_ticket_schema, service_tickets_schema, edit_service_ticket_schema
from app.blueprints.inventory.schemas import add_part_to_ticket_schema
from app.utils.util import mechanic_token_required
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import ServiceTicket, Mechanic, Inventory, ServiceInventory, db
from app.extensions import limiter, cache
from . import service_tickets_bp


# Create A Service Ticket (Requires Mechanic Token)
@service_tickets_bp.route('/', methods=['POST'])
@mechanic_token_required
def create_service_ticket(user_id):
    try:
        new_service_ticket = service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.add(new_service_ticket)
    db.session.commit()
    return service_ticket_schema.jsonify(new_service_ticket), 201


# Get All Service Tickets (With Pagination and Caching)
@service_tickets_bp.route('/', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def get_all_service_tickets():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page', 10))
        query = select(ServiceTicket)
        service_tickets = db.paginate(query, page=page, per_page=per_page)
        return service_tickets_schema.jsonify(service_tickets), 200
    except:
        query = select(ServiceTicket)
        service_tickets = db.session.execute(query).scalars().all()
        return service_tickets_schema.jsonify(service_tickets), 200


# Get a Specific Service Ticket
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
def get_service_ticket(ticket_id):
    service_ticket = db.session.get(ServiceTicket, ticket_id)
    if service_ticket:
        return service_ticket_schema.jsonify(service_ticket), 200
    return jsonify({"message": "Service Ticket not found."}), 404


# Assign Mechanic to Service Ticket (Requires Mechanic Token)
@service_tickets_bp.route('/<int:ticket_id>/assign-mechanic/<int:mechanic_id>', methods=['PUT'])
@mechanic_token_required
def assign_mechanic(user_id, ticket_id, mechanic_id):

    service_ticket = db.session.get(ServiceTicket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service Ticket not found'}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    # Check if mechanic is already assigned
    if mechanic in service_ticket.mechanics:
        return jsonify({'message': 'Mechanic already assigned to this service ticket'}), 400

    # Append mechanic to the service ticket's mechanics list
    service_ticket.mechanics.append(mechanic)
    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket), 200


# Delete Mechanic from Service Ticket (Requires Mechanic Token)
@service_tickets_bp.route('/<int:ticket_id>/remove-mechanic/<int:mechanic_id>', methods=['PUT'])
@mechanic_token_required
def remove_mechanic(user_id, ticket_id, mechanic_id):

    service_ticket = db.session.get(ServiceTicket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service Ticket not found'}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    # Check if mechanic is assigned
    if mechanic not in service_ticket.mechanics:
        return jsonify({'message': 'Mechanic not assigned to this service ticket'}), 400

    # Remove mechanic from the service ticket's mechanics list
    service_ticket.mechanics.remove(mechanic)
    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket), 200


# Delete Service Ticket
@service_tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@limiter.limit("5 per hour")
@mechanic_token_required
def delete_service_ticket(user_id, ticket_id):
    service_ticket = db.session.get(ServiceTicket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service Ticket not found'}), 404

    db.session.delete(service_ticket)
    db.session.commit()
    return jsonify({'message': 'Service Ticket deleted successfully'}), 200


# Edit Service Ticket's Mechanics
@service_tickets_bp.route('/<int:ticket_id>/edit-mechanics', methods=['PUT'])
@mechanic_token_required
def edit_service_ticket_mechanics(user_id, ticket_id):
    try:
        data = edit_service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    service_ticket = db.session.get(ServiceTicket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service Ticket not found'}), 404

    # Add Mechanics
    for mechanic_id in data['add_ids']:
        mechanic = db.session.get(Mechanic, mechanic_id)
        if mechanic and mechanic not in service_ticket.mechanics:
            service_ticket.mechanics.append(mechanic)

    # Remove Mechanics
    for mechanic_id in data['remove_ids']:
        mechanic = db.session.get(Mechanic, mechanic_id)
        if mechanic and mechanic in service_ticket.mechanics:
            service_ticket.mechanics.remove(mechanic)
    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket), 200


# Add Inventory Part To Ticket (Requires Mechanic Token)
@service_tickets_bp.route('/<int:ticket_id>/add-inventory', methods=['POST'])
@mechanic_token_required
def add_inventory_to_ticket(user_id, ticket_id):
    """
    Request Body:
    {
        'inventory_id': int,
        'quantity': int
    }
    """
    try:
        data = add_part_to_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    # Verify Existence Of Ticket & Part
    service_ticket = db.session.get(ServiceTicket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service Ticket not found'}), 404

    inventory = db.session.get(Inventory, data['inventory_id'])
    if not inventory:
        return jsonify({'error': 'Inventory Part not found'}), 404

    # Sufficient Stock Available?
    if inventory.quantity_in_stock < data['quantity']:
        return jsonify({
            'error': 'Insufficient stock',
            'part': inventory.part_name,
            'requested': data['quantity'],
            'available': inventory.quantity_in_stock
        }), 400

    ## Check If Part Already Added To Ticket
    existing = db.session.execute(
        select(ServiceInventory).where(
            ServiceInventory.service_ticket_id == ticket_id,
            ServiceInventory.inventory_id == data['inventory_id']
        )
    ).scalar_one_or_none()

    if existing:
        # Update Quantity
        existing.quantity_used += data['quantity']
        inventory.quantity_in_stock -= data['quantity'] # Deduct From Stock
        db.session.commit()
        return jsonify({
            'message': f'Updated quantity for {inventory.part_name}',
            'part': inventory.part_name,
            'quantity_used': existing.quantity_used,
            'quantity_in_stock': inventory.quantity_in_stock
        }), 200
    else:
        # Create New ServiceInventory Record
        new_service_inventory = ServiceInventory(
            service_ticket_id=ticket_id,
            inventory_id=data['inventory_id'],
            quantity_used=data['quantity']
        )
        inventory.quantity_in_stock -= data['quantity'] # Deduct From Stock
        db.session.add(new_service_inventory)
        db.session.commit()
        return jsonify({
            'message': f'Added {data['quantity']}x {inventory.part_name} to service ticket',
            'part': inventory.part_name,
            'quantity_used': data['quantity'],
            'stock_remaining': inventory.quantity_in_stock
        }), 201


# Remove Inventory Part From Ticket (Restores Stock (Requires Mechanic Token))
@service_tickets_bp.route('/<int:ticket_id>/remove-inventory/<int:inventory_id>', methods=['PUT'])
@mechanic_token_required
def remove_inventory_from_ticket(user_id, ticket_id, service_inventory_id):
    service_inventory = db.session.get(ServiceInventory, service_inventory_id)
    if not service_inventory:
        return jsonify({'error': 'Service Inventory record not found'}), 404

    if service_inventory.service_ticket_id != ticket_id:
        return jsonify({'error': 'Service Inventory does not belong to the specified Service Ticket'}), 400

    # Restore Stock
    inventory = service_inventory.inventory
    inventory.quantity_in_stock += service_inventory.quantity_used
    db.session.delete(service_inventory)
    db.session.commit()
    return jsonify({
        'message': f'Removed {inventory.part_name} from ticket & restored stock',
        'part': inventory.part_name,
        'quantity_restored': service_inventory.quantity_used,
        'stock_remaining': inventory.quantity_in_stock
    }), 200