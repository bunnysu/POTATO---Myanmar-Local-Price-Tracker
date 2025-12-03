#!/usr/bin/env python3
"""
Comprehensive seed script to create test users for all roles
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), 'config.env')
load_dotenv(dotenv_path=config_path)

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.core.security import get_password_hash

def seed_test_users():
    """Seed the database with test users for all roles"""
    db = next(get_postgres_db())
    
    try:
        print("👥 Creating test users for all roles...")
        
        # Test users for all roles
        test_users = [
            # Admin users
            {
                "email": "admin@example.com",
                "full_name": "Admin User",
                "password": "admin123",
                "role": models.UserRole.ADMIN,
                "phone_number": "09-111111111"
            },
            {
                "email": "superadmin@example.com",
                "full_name": "Super Admin",
                "password": "admin123",
                "role": models.UserRole.ADMIN,
                "phone_number": "09-111111112"
            },
            
            # Contributor users
            {
                "email": "contributor@example.com",
                "full_name": "Contributor User",
                "password": "contributor123",
                "role": models.UserRole.CONTRIBUTOR,
                "phone_number": "09-222222221"
            },
            {
                "email": "thida@example.com",
                "full_name": "Ma Thida",
                "password": "contributor123",
                "role": models.UserRole.CONTRIBUTOR,
                "phone_number": "09-222222222"
            },
            
            # Retailer users
            {
                "email": "retailer@example.com",
                "full_name": "Retailer User",
                "password": "retailer123",
                "role": models.UserRole.RETAILER,
                "phone_number": "09-333333331"
            },
            {
                "email": "aung@example.com",
                "full_name": "Ko Aung Aung",
                "password": "retailer123",
                "role": models.UserRole.RETAILER,
                "phone_number": "09-333333332"
            },
            
            # Regular users
            {
                "email": "user@example.com",
                "full_name": "Regular User",
                "password": "user123",
                "role": models.UserRole.USER,
                "phone_number": "09-444444441"
            },
            {
                "email": "kyaw@example.com",
                "full_name": "U Kyaw",
                "password": "user123",
                "role": models.UserRole.USER,
                "phone_number": "09-444444442"
            },
            {
                "email": "mya@example.com",
                "full_name": "Daw Mya",
                "password": "user123",
                "role": models.UserRole.USER,
                "phone_number": "09-444444443"
            },
            {
                "email": "john.doe@test.com",
                "full_name": "John Doe",
                "password": "user123",
                "role": models.UserRole.USER,
                "phone_number": "09-444444444"
            }
        ]
        
        created_users = []
        updated_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(models.User).filter(models.User.email == user_data["email"]).first()
            
            if existing_user:
                print(f"⚠️ User {user_data['email']} already exists (ID: {existing_user.id})")
                # Update the existing user with new data
                existing_user.full_name = user_data["full_name"]
                existing_user.role = user_data["role"]
                existing_user.phone_number = user_data["phone_number"]
                # Update password if it's different
                if not existing_user.hashed_password or existing_user.hashed_password == "dummy":
                    existing_user.hashed_password = get_password_hash(user_data["password"])
                updated_users.append(existing_user)
                print(f"   ✅ Updated user: {user_data['email']} (Role: {user_data['role']})")
            else:
                # Hash password
                hashed_password = get_password_hash(user_data["password"])
                
                # Create user
                new_user = models.User(
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password=hashed_password,
                    phone_number=user_data["phone_number"],
                    role=user_data["role"],
                    status=models.UserStatus.ACTIVE
                )
                
                db.add(new_user)
                db.flush()  # Get the user ID
                created_users.append(new_user)
                print(f"✅ Created user: {user_data['email']} (ID: {new_user.id}, Role: {user_data['role']})")
        
        db.commit()
        
        print(f"\n🎉 Test users creation completed!")
        print(f"📊 Total users created: {len(created_users)}")
        print(f"📊 Total users updated: {len(updated_users)}")
        print(f"📊 Total users available: {len(created_users) + len(updated_users)}")
        
        print("\n📝 User credentials by role:")
        print("\n🔴 ADMIN Users:")
        admin_users = [u for u in created_users + updated_users if u.role == models.UserRole.ADMIN]
        for user in admin_users:
            print(f"   - {user.email} / admin123")
            
        print("\n🟡 CONTRIBUTOR Users:")
        contributor_users = [u for u in created_users + updated_users if u.role == models.UserRole.CONTRIBUTOR]
        for user in contributor_users:
            print(f"   - {user.email} / contributor123")
            
        print("\n🟢 RETAILER Users:")
        retailer_users = [u for u in created_users + updated_users if u.role == models.UserRole.RETAILER]
        for user in retailer_users:
            print(f"   - {user.email} / retailer123")
            
        print("\n🔵 USER Users:")
        user_users = [u for u in created_users + updated_users if u.role == models.UserRole.USER]
        for user in user_users:
            print(f"   - {user.email} / user123")
        
        return created_users + updated_users
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        db.rollback()
        return []
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Starting test users seeding...")
    seed_test_users()












