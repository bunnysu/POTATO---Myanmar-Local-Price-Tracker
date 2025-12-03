#!/usr/bin/env python3
"""
Script to create test users for the reviews system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.core import security

def create_test_users():
    """Create test users for the reviews system"""
    
    db = next(get_postgres_db())
    
    try:
        print("👥 Creating test users for reviews system...")
        
        # Test users to create
        test_users = [
            {
                "email": "john.doe@test.com",
                "full_name": "John Doe",
                "password": "password123",
                "role": models.UserRole.USER,
                "phone_number": "09-111111111"
            },
            {
                "email": "jane.smith@test.com",
                "full_name": "Jane Smith",
                "password": "password123",
                "role": models.UserRole.USER,
                "phone_number": "09-222222222"
            },
            {
                "email": "mike.johnson@test.com",
                "full_name": "Mike Johnson",
                "password": "password123",
                "role": models.UserRole.USER,
                "phone_number": "09-333333333"
            },
            {
                "email": "sarah.wilson@test.com",
                "full_name": "Sarah Wilson",
                "password": "password123",
                "role": models.UserRole.USER,
                "phone_number": "09-444444444"
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(models.User).filter(models.User.email == user_data["email"]).first()
            
            if existing_user:
                print(f"⚠️ User {user_data['email']} already exists (ID: {existing_user.id})")
                created_users.append(existing_user)
            else:
                # Hash password
                hashed_password = security.get_password_hash(user_data["password"])
                
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
                print(f"✅ Created user: {user_data['email']} (ID: {new_user.id})")
        
        db.commit()
        
        print(f"\n🎉 Test users creation completed!")
        print(f"📊 Total users available: {len(created_users)}")
        print("\n📝 User credentials:")
        for user in created_users:
            print(f"   - {user.email} / password123 (ID: {user.id})")
        
        return created_users
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        db.rollback()
        return []
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()

