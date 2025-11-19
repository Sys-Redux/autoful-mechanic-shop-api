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


class EditServiceTicketSchema(ma.Schema):
    add_ids = fields.List(fields.Int(), required=True)
    remove_ids = fields.List(fields.Int(), required=True)

    class Meta:
        fields = ('add_ids', 'remove_ids')

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
edit_service_ticket_schema = EditServiceTicketSchema()