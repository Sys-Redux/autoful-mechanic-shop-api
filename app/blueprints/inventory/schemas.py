from app.models import Inventory, ServiceInventory
from app.extensions import ma
from marshmallow import fields, validate

class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        load_instance = True


class ServiceInventorySchema(ma.SQLAlchemyAutoSchema):
    inventory = fields.Nested('InventorySchema', dump_only=True)
    quantity_used = fields.Int(required=True, validate=validate.Range(min=1))

    class Meta:
        model = ServiceInventory
        load_instance = True
        include_fk = True


class AddPartToTicketSchema(ma.Schema):
    inventory_id = fields.Int(required=True)
    quantity_used = fields.Int(required=True, validate=validate.Range(min=1))


inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
service_inventory_schema = ServiceInventorySchema()
service_inventories_schema = ServiceInventorySchema(many=True)
add_part_to_ticket_schema = AddPartToTicketSchema()