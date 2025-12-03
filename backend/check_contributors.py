#!/usr/bin/env python3
"""
Check what contributor users exist in the database
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

def check_contributors():
    """Check all users and identify contributors"""
    
    print("👥 Checking All Users in Database")
    print("=" * 40)
    
    db = next(get_postgres_db())
    
    try:
        # Get all users
        all_users = db.query(models.User).all()
        
        if not all_users:
            print("❌ No users found in database")
            return
        
        print(f"📊 Total users found: {len(all_users)}")
        print()
        
        for i, user in enumerate(all_users, 1):
            print(f"👤 User {i}:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.full_name or 'N/A'}")
            print(f"   Role: {user.role}")
            print(f"   Status: {user.status}")
            print(f"   Created: {user.created_at}")
            print()
        
        # Count by role
        contributors = [u for u in all_users if u.role == models.UserRole.CONTRIBUTOR]
        users = [u for u in all_users if u.role == models.UserRole.USER]
        admins = [u for u in all_users if u.role == models.UserRole.ADMIN]
        
        print(f"📈 Users by Role:")
        print(f"   Contributors: {len(contributors)}")
        print(f"   Users: {len(users)}")
        print(f"   Admins: {len(admins)}")
        
        if contributors:
            print(f"\n🎯 Contributor accounts:")
            for contrib in contributors:
                print(f"   - {contrib.email} (ID: {contrib.id})")
        
        return all_users
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    check_contributors()
