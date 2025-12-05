from app.models import Mechanic
from app.extensions import ma
from marshmallow import fields, validate

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    service_tickets = fields.Nested('ServiceTicketSchema', many=True, dump_only=True, exclude=('mechanics',))
    password = fields.String(load_only=True, required=True)
    email = fields.Email(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    firebase_uid = fields.String(load_only=True, required=False)

    class Meta:
        model = Mechanic
        load_instance = True
        include_fk = True

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)