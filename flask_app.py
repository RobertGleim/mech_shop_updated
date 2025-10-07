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
    
    # For debugging: Remove any existing user with this email
    try:
        db.session.execute(text("DELETE FROM mechanics WHERE email = 'Robertgleim@email.com'"))
        db.session.commit()
        print("Removed any existing users with that email")
    except Exception as e:
        print(f"Error removing existing users: {e}")
        db.session.rollback()
    
    # Create the default admin mechanic with plain text password
    # (Let the application's login route handle the hashing)
    try:
        # Create with plain text password - many Flask apps expect this in the model
        admin_mechanic = Mechanics(
            first_name='Robert',
            last_name='Gleim',
            email='Robertgleim@email.com',
            password='999',  # Store as plain text - login will handle verification
            salary=75000,
            address='123 fun street',
            is_admin=True
        )
        db.session.add(admin_mechanic)
        db.session.commit()
        print("Default admin mechanic created with plain text password")
        
        # Print verification
        result = db.session.execute(text("SELECT id, email, password FROM mechanics WHERE email = 'Robertgleim@email.com'")).fetchone()
        if result:
            print(f"User created with ID: {result[0]}, Email: {result[1]}, Password: {result[2][:10]}...")
    except Exception as e:
        print(f"Error setting up admin user: {e}")
        db.session.rollback()

#  comment for git push test
