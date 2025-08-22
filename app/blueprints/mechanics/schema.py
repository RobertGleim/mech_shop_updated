from app.extenstions import ma
from app.models import Mechanics

class MechanicsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanics
        include_fk = True
        
mechanic_schema = MechanicsSchema()
mechanics_schema = MechanicsSchema(many=True)
login_schema = MechanicsSchema(only=["email", "password"])