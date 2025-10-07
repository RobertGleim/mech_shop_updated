from app import create_app
from app.models import db, Mechanics

app = create_app('ProductionConfig')

with app.app_context():
    # db.drop_all()  
    db.create_all()   
    
    # Check if default admin mechanic exists
    
    default_mechanic = db.session.execute(
        db.select(Mechanics).filter_by(email='Robertgleim@email.com')
    ).scalar_one_or_none()
    
    if not default_mechanic:
        # Create default admin mechanic
        admin_mechanic = Mechanics(
            first_name='Robert',
            last_name='Gleim',
            email='Robertgleim@email.com',
            password='999',  # Note: In production, use password hashing
            salary=75000,
            address='123 fun street',
            is_admin=True
        )
        db.session.add(admin_mechanic)
        db.session.commit()
        print("Default admin mechanic created")

#  comment for git push test
