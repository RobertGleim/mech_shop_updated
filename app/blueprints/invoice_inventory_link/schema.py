from app.extenstions import ma
from app.models import Invoice_Inventory_link

class Invoice_Inventory_link_Schema(ma.SQLAlchemyAutoSchema):
   
    class Meta:
        model = Invoice_Inventory_link
        include_fk = True
        
invoice_inventory_link_schema = Invoice_Inventory_link_Schema()
invoices_invenotorys_link_schema = Invoice_Inventory_link_Schema(many=True)