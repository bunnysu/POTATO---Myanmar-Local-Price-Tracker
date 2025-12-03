#!/usr/bin/env python3
"""
Seed script to add a new admin user to the database.
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=config_path)

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.core.security import get_password_hash

# Admin user credentials
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpassword"

def seed_admin():
    """Seed the database with a new admin user"""
    db = next(get_postgres_db())
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(models.User).filter(models.User.email == ADMIN_EMAIL).first()
        if existing_admin:
            print(f"Admin user with email {ADMIN_EMAIL} already exists. Deleting and recreating...")
            db.delete(existing_admin)
            db.commit()

        # Hash the password
        hashed_password = get_password_hash(ADMIN_PASSWORD)

        # Create the new admin user
        new_admin = models.User(
            email=ADMIN_EMAIL,
            hashed_password=hashed_password,
            full_name="Admin User",
            role=models.UserRole.ADMIN,
            status=models.UserStatus.ACTIVE
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        print(f"Admin user {ADMIN_EMAIL} created successfully.")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding admin user...")
    seed_admin()