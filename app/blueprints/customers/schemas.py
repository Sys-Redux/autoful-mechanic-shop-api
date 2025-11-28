from app.models import Customer
from app.extensions import ma
from marshmallow import fields, validate


class CustomerSchema(ma.SQLAlchemyAutoSchema):
    service_tickets = fields.Nested('ServiceTicketSchema', many=True, dump_only=True, exclude=('customer',))
    password = fields.String(load_only=True, required=True)
    email = fields.Email(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))

    class Meta:
        model = Customer
        load_instance = True
        include_fk = True

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)