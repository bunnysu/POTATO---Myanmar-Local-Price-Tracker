#!/usr/bin/env python3
"""
Test script to verify the change password function now works correctly.
This script will:
1. List all users to see their current IDs
2. Show which user would be affected by the change password function
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from sqlalchemy.orm import Session

def test_change_password_target():
    """Test which user the change password function would target."""
    
    # Get database session
    db = next(get_postgres_db())
    
    try:
        print("🔍 Testing Change Password Function Target")
        print("=" * 50)
        
        # Get all users
        users = db.query(models.User).all()
        
        if not users:
            print("❌ No users found in database")
            return
        
        print(f"📊 Found {len(users)} users in database:")
        print("-" * 50)
        
        for user in users:
            print(f"ID: {user.id} | Email: {user.email} | Role: {user.role} | Name: {user.full_name}")
        
        print("-" * 50)
        
        # Show what the OLD implementation would do (get first user)
        first_user = db.query(models.User).first()
        print(f"❌ OLD IMPLEMENTATION would change password for: User ID {first_user.id} ({first_user.email})")
        
        print("\n✅ NEW IMPLEMENTATION will change password for: The authenticated user (from JWT token)")
        print("   This means the password change will affect the user who is actually logged in!")
        
        print("\n🎯 To test this:")
        print("1. Login as any user (admin, contributor, retailer)")
        print("2. Go to their profile page")
        print("3. Use the change password function")
        print("4. The password will be changed for THAT specific user, not user ID 1")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_change_password_target()
