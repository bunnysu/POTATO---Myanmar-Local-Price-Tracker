#!/usr/bin/env python3
"""
Reset user password to a known value for testing
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv(dotenv_path='config.env')

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.core.security import get_password_hash

def reset_password():
    """Reset contributor's password to 'contributor123'"""
    
    print("🔧 Resetting Contributor Password to Known Value")
    print("=" * 50)
    
    db = next(get_postgres_db())
    
    try:
        # Look for contributor users first
        contributor = db.query(models.User).filter(models.User.role == models.UserRole.CONTRIBUTOR).first()
        
        if not contributor:
            # If no contributor, look for regular users
            contributor = db.query(models.User).filter(models.User.role == models.UserRole.USER).first()
        
        if not contributor:
            # If still no user, get any user
            contributor = db.query(models.User).first()
            
        if not contributor:
            print("❌ No users found in database")
            return False
        
        # Set password to known value for contributor
        new_password = "contributor123"
        hashed_password = get_password_hash(new_password)
        
        print(f"📝 Resetting password for contributor: {contributor.email}")
        print(f"📝 Role: {contributor.role}")
        print(f"📝 New password: {new_password}")
        
        # Update password
        contributor.hashed_password = hashed_password
        db.commit()
        
        print(f"✅ Password reset successfully!")
        print(f"\n🔑 Contributor Login credentials:")
        print(f"   Email: {contributor.email}")
        print(f"   Password: {new_password}")
        print(f"   Role: {contributor.role}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
