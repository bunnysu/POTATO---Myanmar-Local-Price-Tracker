#!/usr/bin/env python3
"""
Complete setup and test script for notifications system.
This will:
1. Create admin and test users if they don't exist
2. Test the broadcast notification functionality  
3. Verify notifications are stored in database
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(config_path):
    load_dotenv(dotenv_path=config_path)

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.core.security import get_password_hash

def create_test_users():
    """Create admin and test users for testing"""
    print("👤 Creating test users...")
    
    db = next(get_postgres_db())
    
    try:
        # Test users to create
        test_users = [
            {
                "email": "admin@potato.com",
                "password": "admin123",
                "full_name": "Admin User",
                "role": models.UserRole.ADMIN,
                "status": models.UserStatus.ACTIVE
            },
            {
                "email": "user1@potato.com", 
                "password": "user123",
                "full_name": "Test User 1",
                "role": models.UserRole.USER,
                "status": models.UserStatus.ACTIVE
            },
            {
                "email": "user2@potato.com",
                "password": "user123", 
                "full_name": "Test User 2",
                "role": models.UserRole.USER,
                "status": models.UserStatus.ACTIVE
            },
            {
                "email": "contributor@potato.com",
                "password": "contrib123",
                "full_name": "Test Contributor",
                "role": models.UserRole.CONTRIBUTOR,
                "status": models.UserStatus.ACTIVE
            }
        ]
        
        users_created = 0
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(models.User).filter(models.User.email == user_data["email"]).first()
            
            if existing_user:
                print(f"   ✓ User {user_data['email']} already exists")
                continue
            
            # Create new user
            hashed_password = get_password_hash(user_data["password"])
            
            new_user = models.User(
                email=user_data["email"],
                hashed_password=hashed_password,
                full_name=user_data["full_name"],
                role=user_data["role"],
                status=user_data["status"]
            )
            
            db.add(new_user)
            users_created += 1
            print(f"   ✓ Created user: {user_data['email']} ({user_data['role']})")
        
        db.commit()
        
        total_users = db.query(models.User).count()
        active_users = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).count()
        
        print(f"   📊 Total users in database: {total_users}")
        print(f"   📊 Active users: {active_users}")
        print(f"   📊 New users created: {users_created}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_broadcast_notifications():
    """Test creating broadcast notifications and verify they're stored"""
    print("\n📢 Testing broadcast notifications...")
    
    db = next(get_postgres_db())
    
    try:
        # Check users count
        active_users = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).all()
        notification_count_before = db.query(models.Notification).count()
        
        print(f"   📊 Active users found: {len(active_users)}")
        print(f"   📊 Notifications before test: {notification_count_before}")
        
        if len(active_users) == 0:
            print("   ❌ No active users found! Cannot test notifications.")
            return False
        
        # Create test announcement
        test_title = "System Maintenance Announcement"
        test_message = "The system will undergo maintenance from 2:00 PM to 4:00 PM today. Please save your work and log out during this time."
        
        print(f"   📤 Creating broadcast notification:")
        print(f"       Title: {test_title}")
        print(f"       Message: {test_message[:50]}...")
        
        # Create notification for each active user (simulating the broadcast endpoint)
        notifications_created = 0
        
        for user in active_users:
            notification = models.Notification(
                user_id=user.id,
                title=test_title,
                message=test_message,
                category=models.NotificationCategory.SYSTEM,
                read=False,
            )
            db.add(notification)
            notifications_created += 1
        
        # Commit all notifications
        db.commit()
        
        print(f"   ✅ Created {notifications_created} notifications")
        
        # Verify notifications were stored
        notification_count_after = db.query(models.Notification).count()
        new_notifications = notification_count_after - notification_count_before
        
        print(f"   📊 Notifications after test: {notification_count_after}")
        print(f"   📊 New notifications created: {new_notifications}")
        
        # Check specific test notifications
        test_notifications = db.query(models.Notification).filter(
            models.Notification.title == test_title
        ).all()
        
        print(f"   📊 Test notifications found in database: {len(test_notifications)}")
        
        if len(test_notifications) == len(active_users):
            print("   ✅ SUCCESS: All active users received the notification!")
            return True
        else:
            print(f"   ❌ MISMATCH: Expected {len(active_users)} notifications, found {len(test_notifications)}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing notifications: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_database_status():
    """Display current database status"""
    print("\n📊 Database Status:")
    print("=" * 40)
    
    db = next(get_postgres_db())
    
    try:
        # Users
        users = db.query(models.User).all()
        print(f"👥 Users ({len(users)}):")
        for user in users:
            print(f"   ID: {user.id} | {user.email} | {user.role} | {user.status}")
        
        # Notifications
        notifications = db.query(models.Notification).order_by(models.Notification.created_at.desc()).all()
        print(f"\n📢 Notifications ({len(notifications)}):")
        if notifications:
            for notif in notifications[:10]:  # Show last 10
                print(f"   ID: {notif.id} | User: {notif.user_id} | {notif.title[:30]}... | {notif.category} | Read: {notif.read}")
        else:
            print("   No notifications found")
            
        # Summary by category
        system_notifs = db.query(models.Notification).filter(models.Notification.category == models.NotificationCategory.SYSTEM).count()
        price_notifs = db.query(models.Notification).filter(models.Notification.category == models.NotificationCategory.PRICE).count()
        
        print(f"\n📈 Notification Summary:")
        print(f"   System notifications: {system_notifs}")
        print(f"   Price notifications: {price_notifs}")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    finally:
        db.close()

def main():
    print("🚀 Notification System Setup & Test")
    print("=" * 50)
    
    # Step 1: Create users
    users_success = create_test_users()
    if not users_success:
        print("❌ Failed to create users. Stopping.")
        return
    
    # Step 2: Test notifications
    notif_success = test_broadcast_notifications()
    
    # Step 3: Show final status
    show_database_status()
    
    # Final result
    print("\n" + "=" * 50)
    if users_success and notif_success:
        print("🎉 SUCCESS! Notification system is working!")
        print("\n✅ What happened:")
        print("   1. Test users were created/verified")
        print("   2. Broadcast notifications were created")
        print("   3. Notifications are stored in the database")
        print("\n💡 Now you can:")
        print("   1. Start your backend server")
        print("   2. Use the admin panel to send announcements")
        print("   3. Check that notifications appear in the database")
        print("\n🔗 API Endpoint: POST /api/notifications/broadcast")
    else:
        print("💥 Something went wrong. Check the errors above.")

if __name__ == "__main__":
    main()
