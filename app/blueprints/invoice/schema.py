from app.extenstions import ma
from app.models import Invoice

class InvoiceSchema(ma.SQLAlchemyAutoSchema):
   
    class Meta:
        model = Invoice
        include_fk = True
        
invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)