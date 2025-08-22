from app.extenstions import ma
from app.models import Customers

class  CustomerSchema(ma.SQLAlchemyAutoSchema):
   
    class Meta:
        model = Customers
        include_fk = True
        
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
login_schema = CustomerSchema(only=["email", "password"])
