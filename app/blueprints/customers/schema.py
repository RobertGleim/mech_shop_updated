from app.extenstions import ma
from app.models import Customers
from marshmallow import fields

class  CustomerSchema(ma.SQLAlchemyAutoSchema):
    email = fields.Email(required=True)  
   
    class Meta:
        model = Customers
        include_fk = True
        
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
login_schema = CustomerSchema(only=["email", "password"])
