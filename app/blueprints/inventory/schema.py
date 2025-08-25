from app.extenstions import ma
from app.models import Inventory

class InventorySchema(ma.SQLAlchemyAutoSchema):
   
    class Meta:
        model = Inventory
        include_fk = True
        
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
