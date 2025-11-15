from app.models import ServiceTicket
from app.extensions import ma
from marshmallow import fields

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    customer = fields.Nested('CustomerSchema', dump_only=True, exclude=('service_tickets',))
    mechanics = fields.Nested('MechanicSchema', many=True, dump_only=True, exclude=('service_tickets',))

    class Meta:
        model = ServiceTicket
        load_instance = True
        include_fk = True

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)