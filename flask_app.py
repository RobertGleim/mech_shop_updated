from app import create_app
from app.models import db, Mechanics
from sqlalchemy import text

app = create_app('ProductionConfig')

with app.app_context():
    # First, check if is_admin column exists and add it if missing
    try:
        # Try to add the column if it doesn't exist
        db.session.execute(text("ALTER TABLE mechanics ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"))
        db.session.commit()
        print("Checked/added is_admin column")
    except Exception as e:
        print(f"Error checking/adding column: {e}")
        db.session.rollback()
    
    # Now continue with the normal initialization
    db.create_all()   
    
    # Check if default admin mechanic exists
    try:
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
    except Exception as e:
        print(f"Error setting up admin user: {e}")
        db.session.rollback()

#  comment for git push test
