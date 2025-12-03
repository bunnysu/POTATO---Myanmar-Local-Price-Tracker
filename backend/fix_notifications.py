#!/usr/bin/env python3
"""
Simple script to fix the empty notifications table issue.
This will create users and test notifications.
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

print("🔧 Fixing Notifications Table Issue")
print("=" * 40)

db = next(get_postgres_db())

try:
    # Step 1: Check current database state
    user_count = db.query(models.User).count()
    notification_count = db.query(models.Notification).count()
    
    print(f"📊 Current users: {user_count}")
    print(f"📊 Current notifications: {notification_count}")
    
    # Step 2: Create users if none exist
    if user_count == 0:
        print("\n👤 Creating test users...")
        
        # Create admin user
        admin_password = get_password_hash("admin123")
        admin = models.User(
            email="admin@potato.com",
            hashed_password=admin_password,
            full_name="Admin User",
            role=models.UserRole.ADMIN,
            status=models.UserStatus.ACTIVE
        )
        db.add(admin)
        
        # Create regular users
        user1_password = get_password_hash("user123")
        user1 = models.User(
            email="user1@potato.com",
            hashed_password=user1_password,
            full_name="Test User 1",
            role=models.UserRole.USER,
            status=models.UserStatus.ACTIVE
        )
        db.add(user1)
        
        user2_password = get_password_hash("user123")
        user2 = models.User(
            email="user2@potato.com",
            hashed_password=user2_password,
            full_name="Test User 2",
            role=models.UserRole.USER,
            status=models.UserStatus.ACTIVE
        )
        db.add(user2)
        
        db.commit()
        print("✅ Created 3 test users (1 admin, 2 users)")
    else:
        print("✅ Users already exist")
    
    # Step 3: Create test notifications
    print("\n📢 Creating test notifications...")
    
    # Get all active users
    active_users = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).all()
    
    if len(active_users) == 0:
        print("❌ No active users found!")
    else:
        # Create a system announcement for all users
        announcement_title = "Welcome to Potato Price System"
        announcement_message = "Welcome! This is a test system announcement. You can now track prices and get notifications when items you're watching change price."
        
        notifications_created = 0
        for user in active_users:
            # Create system notification
            notification = models.Notification(
                user_id=user.id,
                title=announcement_title,
                message=announcement_message,
                category=models.NotificationCategory.SYSTEM,
                read=False,
            )
            db.add(notification)
            notifications_created += 1
            
            # Create a price notification example too
            price_notification = models.Notification(
                user_id=user.id,
                title="Price Alert: Rice",
                message="The price of Rice has changed to 1500 MMK at Golden Shop. Check it out!",
                category=models.NotificationCategory.PRICE,
                read=False,
            )
            db.add(price_notification)
            notifications_created += 1
        
        db.commit()
        print(f"✅ Created {notifications_created} test notifications")
    
    # Step 4: Show final results
    final_user_count = db.query(models.User).count()
    final_notification_count = db.query(models.Notification).count()
    
    print(f"\n📊 Final Results:")
    print(f"   Users: {final_user_count}")
    print(f"   Notifications: {final_notification_count}")
    
    # Show some example notifications
    sample_notifications = db.query(models.Notification).limit(5).all()
    print(f"\n📝 Sample notifications:")
    for notif in sample_notifications:
        print(f"   ID: {notif.id} | User: {notif.user_id} | {notif.title} | {notif.category}")
    
    print(f"\n🎉 SUCCESS! Your notifications table now has data!")
    print(f"📋 Next steps:")
    print(f"   1. Start your backend server: uvicorn app.main:app --reload")
    print(f"   2. Test the broadcast endpoint: POST /api/notifications/broadcast")
    print(f"   3. Check your frontend can send announcements")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
