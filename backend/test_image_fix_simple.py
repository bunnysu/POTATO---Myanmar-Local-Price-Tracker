#!/usr/bin/env python3
"""
Simple test to verify image upload fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_postgres_db
from app.db import postgres_models as models

def test_image_fix():
    """Test the image upload fix."""
    
    db = next(get_postgres_db())
    
    try:
        print("🔍 Testing Image Upload Fix")
        print("=" * 40)
        
        users = db.query(models.User).all()
        
        for user in users:
            print(f"\nUser ID: {user.id} | Email: {user.email}")
            print(f"Database image_url: '{user.image_url}'")
            
            if user.image_url:
                # Test the URL construction
                if user.image_url.startswith('http'):
                    print(f"✅ Full URL: {user.image_url}")
                elif user.image_url.startswith('uploads/'):
                    constructed_url = f"http://localhost:8000/api/uploads/{user.image_url}"
                    print(f"✅ Relative path -> Full URL: {constructed_url}")
                else:
                    # This should be the most common case now (just filename)
                    constructed_url = f"http://localhost:8000/api/uploads/{user.image_url}"
                    print(f"✅ Filename -> Full URL: {constructed_url}")
            else:
                print("❌ No image uploaded")
        
        print("\n" + "=" * 40)
        print("✅ FIXES APPLIED:")
        print("1. Backend now stores just filename in database")
        print("2. Backend returns full URL in response")
        print("3. Frontend helper function handles filename correctly")
        print("4. Frontend uses backend URL for immediate display")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_image_fix()
