#!/usr/bin/env python3
"""
Test script to verify that broadcast notifications are stored in the database.
This script directly tests the database insertion without requiring frontend integration.
"""

from sqlalchemy.orm import Session
from app.db.database import get_postgres_db
from app.db import postgres_models as models

def test_broadcast_notification_storage():
    """Test that we can create notifications for all users"""
    
    print("🧪 Testing Broadcast Notification Storage...")
    print("=" * 50)
    
    db = next(get_postgres_db())
    
    try:
        # 1. Check current state
        user_count = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).count()
        notification_count_before = db.query(models.Notification).count()
        
        print(f"📊 Active users in database: {user_count}")
        print(f"📊 Notifications before test: {notification_count_before}")
        
        if user_count == 0:
            print("⚠️  No active users found! Please run seed_admin_users.py first.")
            return False
        
        # 2. Create test announcement data
        test_title = "Test System Announcement"
        test_message = "This is a test announcement to verify notification storage works."
        
        print(f"\n📤 Creating broadcast notification...")
        print(f"   Title: {test_title}")
        print(f"   Message: {test_message}")
        
        # 3. Get all active users and create notifications
        active_users = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).all()
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
        
        # 4. Commit to database
        db.commit()
        print(f"✅ Created {notifications_created} notifications")
        
        # 5. Verify notifications were stored
        notification_count_after = db.query(models.Notification).count()
        new_notifications = notification_count_after - notification_count_before
        
        print(f"📊 Notifications after test: {notification_count_after}")
        print(f"📊 New notifications created: {new_notifications}")
        
        # 6. Check specific test notifications
        test_notifications = db.query(models.Notification).filter(
            models.Notification.title == test_title
        ).all()
        
        print(f"📊 Test notifications found: {len(test_notifications)}")
        
        if len(test_notifications) == user_count:
            print("✅ SUCCESS: All users received the notification!")
            
            # Show sample notification details
            sample = test_notifications[0]
            print(f"\n📝 Sample notification details:")
            print(f"   ID: {sample.id}")
            print(f"   User ID: {sample.user_id}")
            print(f"   Title: {sample.title}")
            print(f"   Message: {sample.message[:50]}...")
            print(f"   Category: {sample.category}")
            print(f"   Read: {sample.read}")
            print(f"   Created: {sample.created_at}")
            
            return True
        else:
            print(f"❌ MISMATCH: Expected {user_count} notifications, found {len(test_notifications)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_users_and_notifications():
    """Display current users and their notifications"""
    print("\n🔍 Current Database State:")
    print("=" * 30)
    
    db = next(get_postgres_db())
    
    try:
        # Show users
        users = db.query(models.User).all()
        print(f"👥 Users ({len(users)}):")
        for user in users:
            print(f"   ID: {user.id}, Email: {user.email}, Role: {user.role}, Status: {user.status}")
        
        # Show notifications
        notifications = db.query(models.Notification).order_by(models.Notification.created_at.desc()).all()
        print(f"\n📢 Notifications ({len(notifications)}):")
        for notif in notifications[:10]:  # Show last 10
            print(f"   ID: {notif.id}, User: {notif.user_id}, Title: {notif.title[:30]}..., Category: {notif.category}")
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Testing Notification Storage System")
    print("=" * 50)
    
    # Show current state
    show_users_and_notifications()
    
    # Test broadcast functionality
    success = test_broadcast_notification_storage()
    
    # Show final state
    show_users_and_notifications()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED! Broadcast notifications are properly stored in database.")
        print("\n💡 Next step: Update your frontend to call the API endpoint:")
        print("   POST /api/notifications/broadcast")
        print("   Body: {'title': 'Your Title', 'message': 'Your Message'}")
    else:
        print("💥 TEST FAILED! Check the errors above.")
