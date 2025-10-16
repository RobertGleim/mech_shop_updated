from app import create_app
from app.models import db, Mechanics
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash  # Import password hashing function
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use environment variable to determine config, default to DevelopmentConfig (was ProductionConfig)
config_name = os.environ.get('FLASK_CONFIG', 'DevelopmentConfig')
app = create_app(config_name)

with app.app_context():
    # First, check if is_admin column exists and add it if missing
    try:
        # Try to inspect existing columns first (portable across DB backends)
        cols = []
        try:
            inspector = inspect(db.engine)
            cols = [c['name'] for c in inspector.get_columns('mechanics')]
        except Exception:
            # Fallback for SQLite or if inspector isn't available
            try:
                result = db.session.execute(text("PRAGMA table_info('mechanics')")).fetchall()
                cols = [row[1] for row in result]
            except Exception as inner_e:
                # Could not determine mechanics table columns
                cols = []

        if 'is_admin' not in cols:
            # Add column using a dialect-appropriate SQL statement
            dialect = getattr(db.engine, 'dialect', None)
            dialect_name = getattr(dialect, 'name', '') if dialect else ''
            if dialect_name == 'sqlite':
                add_stmt = "ALTER TABLE mechanics ADD COLUMN is_admin INTEGER DEFAULT 0"
            elif dialect_name in ('postgresql', 'postgres'):
                add_stmt = "ALTER TABLE mechanics ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"
            else:
                # Generic boolean fallback
                add_stmt = "ALTER TABLE mechanics ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"

            try:
                db.session.execute(text(add_stmt))
                db.session.commit()
            except Exception as add_err:
                db.session.rollback()
        else:
            pass
    except Exception as e:
        db.session.rollback()
    
    # Now continue with the normal initialization
    db.create_all()   
    
    # For debugging: Remove any existing user with this email (case insensitive)
    try:
        db.session.execute(text("DELETE FROM mechanics WHERE LOWER(email) = LOWER('robertgleim@email.com')"))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    
    # Create the default admin mechanic with hashed password
    try:
        # Using a properly hashed password with Werkzeug
        hashed_password = generate_password_hash('999')
        
        admin_mechanic = Mechanics(
            first_name='Robert',
            last_name='Gleim',
            email='robertgleim@email.com',  # Using lowercase consistently
            password=hashed_password,  # Store as hashed password
            salary=75000,
            address='123 fun street',
            is_admin=True  # <-- Ensure this is True
        )
        db.session.add(admin_mechanic)
        db.session.commit()
        
        # Print verification
        result = db.session.execute(text("SELECT id, email, password FROM mechanics WHERE email = 'robertgleim@email.com'")).fetchone()
        if result:
            pass
    except Exception as e:
        db.session.rollback()

#  comment for git push test

# {
#   "message": "Login successful Robert Gleim",
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTk4NTkwNDYsImlhdCI6MTc1OTg1NTQ0Niwic3ViIjoiNSIsInJvbGUiOiJtZWNoYW5pYyJ9.3Nd5D6evskBCl86wabLZ0o6rMMQxWwFz1yhtkanUVyA"
# }
# comment for git push test


