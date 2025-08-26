from app.extenstions import ma
from app.models import ItemsDescription

class Item_Description(ma.SQLAlchemyAutoSchema):
   
    class Meta:
        model = ItemsDescription
        include_fk = True
        
item_description_schema = Item_Description()
item_descriptions_schema = Item_Description(many=True)