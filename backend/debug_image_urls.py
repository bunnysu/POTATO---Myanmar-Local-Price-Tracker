#!/usr/bin/env python3
"""
Debug script to check image URL issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_postgres_db
from app.db import postgres_models as models

def debug_image_urls():
    """Debug image URL issues."""
    
    db = next(get_postgres_db())
    
    try:
        print("🔍 Debugging Image URL Issues")
        print("=" * 50)
        
        users = db.query(models.User).all()
        
        for user in users:
            print(f"\nUser ID: {user.id} | Email: {user.email}")
            print(f"Database image_url: '{user.image_url}'")
            
            if user.image_url:
                # Test different URL construction methods
                print("Testing URL construction:")
                
                # Method 1: Direct use (what frontend might be doing)
                print(f"  1. Direct: {user.image_url}")
                
                # Method 2: Frontend helper function logic
                if user.image_url.startswith('http'):
                    print(f"  2. Full URL (starts with http): {user.image_url}")
                elif user.image_url.startswith('uploads/'):
                    constructed_url = f"http://localhost:8000/api/uploads/{user.image_url}"
                    print(f"  3. Relative path (starts with uploads/): {constructed_url}")
                else:
                    constructed_url = f"http://localhost:8000/api/uploads/uploads/{user.image_url}"
                    print(f"  4. Filename only: {constructed_url}")
                
                # Method 3: Backend API endpoint
                api_url = f"http://localhost:8000/api/uploads/{user.image_url}"
                print(f"  5. Backend API: {api_url}")
                
            else:
                print("  No image uploaded")
        
        print("\n" + "=" * 50)
        print("POSSIBLE ISSUES:")
        print("1. Check if the image file actually exists in the uploads directory")
        print("2. Check if the URL construction matches between frontend and backend")
        print("3. Check if the backend API endpoint is working")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_image_urls()
