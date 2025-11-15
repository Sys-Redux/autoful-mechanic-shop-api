from app.models import Customer
from app.extensions import ma
from marshmallow import fields


class CustomerSchema(ma.SQLAlchemyAutoSchema):
    service_tickets = fields.Nested('ServiceTicketSchema', many=True, dump_only=True, exclude=('customer',))

    class Meta:
        model = Customer
        load_instance = True
        include_fk = True

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)