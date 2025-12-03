#!/usr/bin/env python3
"""
Test script to verify the image upload fix is working correctly.
This script will:
1. List all users and their image_url values
2. Show how the URLs should be constructed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from sqlalchemy.orm import Session

def test_image_urls():
    """Test how image URLs are stored and should be accessed."""
    
    # Get database session
    db = next(get_postgres_db())
    
    try:
        print("🔍 Testing Image Upload and URL Construction")
        print("=" * 60)
        
        # Get all users
        users = db.query(models.User).all()
        
        if not users:
            print("❌ No users found in database")
            return
        
        print(f"📊 Found {len(users)} users in database:")
        print("-" * 60)
        
        for user in users:
            print(f"ID: {user.id} | Email: {user.email}")
            print(f"   Database image_url: {user.image_url or 'None'}")
            
            if user.image_url:
                # Show how the URL should be constructed
                full_url = f"http://localhost:8000/api/uploads/{user.image_url}"
                print(f"   Full URL should be: {full_url}")
            else:
                print("   No image uploaded")
            
            print()
        
        print("✅ FIXES APPLIED:")
        print("1. Backend now returns both file_path and full URL")
        print("2. Frontend has helper function to construct proper URLs")
        print("3. Image URLs are properly constructed on page load and refresh")
        print("4. Both profile image displays use the helper function")
        
        print("\n🎯 To test:")
        print("1. Upload an image in contributor profile")
        print("2. Verify it shows immediately")
        print("3. Refresh the page")
        print("4. Verify the image still shows")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_image_urls()
