#!/usr/bin/env python3
"""
Test script to verify system announcements are working and storing in database
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

def check_notifications_before_and_after():
    """Check notifications in database and show the difference"""
    
    print("🔍 Checking Notifications Database")
    print("=" * 40)
    
    db = next(get_postgres_db())
    
    try:
        # Count current notifications
        total_notifications = db.query(models.Notification).count()
        system_notifications = db.query(models.Notification).filter(
            models.Notification.category == models.NotificationCategory.SYSTEM
        ).count()
        price_notifications = db.query(models.Notification).filter(
            models.Notification.category == models.NotificationCategory.PRICE
        ).count()
        
        active_users = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).count()
        
        print(f"📊 Current Database State:")
        print(f"   Total notifications: {total_notifications}")
        print(f"   SYSTEM notifications: {system_notifications}")
        print(f"   PRICE notifications: {price_notifications}")
        print(f"   Active users: {active_users}")
        
        # Show recent system notifications
        recent_system = db.query(models.Notification).filter(
            models.Notification.category == models.NotificationCategory.SYSTEM
        ).order_by(models.Notification.created_at.desc()).limit(3).all()
        
        print(f"\n📢 Recent System Notifications:")
        if recent_system:
            for notif in recent_system:
                print(f"   📅 {notif.created_at}: {notif.title}")
                print(f"      User: {notif.user_id} | Read: {notif.read}")
        else:
            print("   ❌ No system notifications found!")
            print("   This means announcements from System Settings are not being saved.")
        
        # Instructions
        print(f"\n💡 To test System Announcements:")
        print(f"   1. Make sure your backend server is running")
        print(f"   2. Go to admin frontend: System Settings > Announcements")
        print(f"   3. Create an announcement with title and message")
        print(f"   4. Click 'Publish Announcement'")
        print(f"   5. Run this script again to see if SYSTEM notifications increased")
        
        return {
            'total': total_notifications,
            'system': system_notifications,
            'price': price_notifications,
            'users': active_users
        }
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        db.close()

def create_test_system_notification():
    """Create a test system notification to verify the functionality"""
    
    print(f"\n🧪 Creating Test System Notification")
    print("=" * 40)
    
    db = next(get_postgres_db())
    
    try:
        # Get active users
        active_users = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).all()
        
        if not active_users:
            print("❌ No active users found! Cannot create notifications.")
            print("   Run: python seed_admin_users.py")
            return False
        
        print(f"👥 Found {len(active_users)} active users")
        
        # Create test announcement (same as what the API would do)
        test_title = "Test System Announcement"
        test_message = "This is a test announcement created directly to verify the system works. If you see this, the notification storage is working correctly!"
        
        print(f"📝 Creating announcement:")
        print(f"   Title: {test_title}")
        print(f"   Message: {test_message[:50]}...")
        
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
        
        db.commit()
        
        print(f"✅ Created {notifications_created} system notifications")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test notification: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 System Announcements Test")
    print("=" * 50)
    
    # Check current state
    before_stats = check_notifications_before_and_after()
    
    if before_stats and before_stats['system'] == 0:
        print(f"\n❓ No system notifications found. Creating a test one...")
        create_test_system_notification()
        
        # Check again
        print(f"\n" + "=" * 50)
        after_stats = check_notifications_before_and_after()
        
        if after_stats and after_stats['system'] > before_stats['system']:
            print(f"\n🎉 SUCCESS! System notifications are working!")
            print(f"   Before: {before_stats['system']} system notifications")
            print(f"   After: {after_stats['system']} system notifications")
        else:
            print(f"\n💥 Something went wrong with notification creation")
    else:
        print(f"\n✅ System notifications found! The announcement system is working.")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Start your servers (backend and frontend)")
    print(f"   2. Test creating announcements from the admin panel")
    print(f"   3. Run this script again to verify new notifications are saved")
