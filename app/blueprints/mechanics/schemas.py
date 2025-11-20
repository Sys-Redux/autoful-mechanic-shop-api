from app.models import Mechanic
from app.extensions import ma
from marshmallow import fields

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    service_tickets = fields.Nested('ServiceTicketSchema', many=True, dump_only=True, exclude=('mechanics',))
    password = fields.String(load_only=True, required=True)

    class Meta:
        model = Mechanic
        load_instance = True
        include_fk = True

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)