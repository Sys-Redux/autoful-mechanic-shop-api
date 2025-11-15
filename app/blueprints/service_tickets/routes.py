from .schemas import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import ServiceTicket, Mechanic, db
from . import service_tickets_bp


# Create A Service Ticket
@service_tickets_bp.route('/', methods=['POST'])
def create_service_ticket():
    try:
        new_service_ticket = service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.add(new_service_ticket)
    db.session.commit()
    return service_ticket_schema.jsonify(new_service_ticket), 201


# Get All Service Tickets
@service_tickets_bp.route('/', methods=['GET'])
def get_all_service_tickets():
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


# Assign Mechanic to Service Ticket
@service_tickets_bp.route('/<int:ticket_id>/assign-mechanic/<int:mechanic_id>', methods=['PUT'])
def assign_mechanic(ticket_id, mechanic_id):

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


# Delete Mechanic from Service Ticket
@service_tickets_bp.route('/<int:ticket_id>/remove-mechanic/<int:mechanic_id>', methods=['DELETE'])
def remove_mechanic(ticket_id, mechanic_id):

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
def delete_service_ticket(ticket_id):
    service_ticket = db.session.get(ServiceTicket, ticket_id)
    if not service_ticket:
        return jsonify({'error': 'Service Ticket not found'}), 404

    db.session.delete(service_ticket)
    db.session.commit()
    return jsonify({'message': 'Service Ticket deleted successfully'}), 200