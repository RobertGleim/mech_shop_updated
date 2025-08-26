from app.extenstions import ma
from app.models import InventoryItem

class InventorySchema(ma.SQLAlchemyAutoSchema):
   
    class Meta:
        model = InventoryItem
        include_fk = True
        
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
