from app import create_app
from app.models import db, Mechanics
from sqlalchemy import text
from werkzeug.security import generate_password_hash  # Import password hashing function

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
            # Create default admin mechanic with properly hashed password
            hashed_password = generate_password_hash('999')
            admin_mechanic = Mechanics(
                first_name='Robert',
                last_name='Gleim',
                email='Robertgleim@email.com',
                password=hashed_password,  # Store the hashed password
                salary=75000,
                address='123 fun street',
                is_admin=True
            )
            db.session.add(admin_mechanic)
            db.session.commit()
            print("Default admin mechanic created with hashed password")
    except Exception as e:
        print(f"Error setting up admin user: {e}")
        db.session.rollback()

#  comment for git push test
