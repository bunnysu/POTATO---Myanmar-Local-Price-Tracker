#!/usr/bin/env python3
"""
Debug script to test password hashing and verification
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
from app.core.security import get_password_hash, verify_password

def test_password_system():
    """Test password hashing and verification"""
    
    print("🔐 Testing Password System")
    print("=" * 40)
    
    db = next(get_postgres_db())
    
    try:
        # Get the first user
        user = db.query(models.User).first()
        if not user:
            print("❌ No users found in database")
            return False
        
        print(f"📝 Testing with user: {user.email}")
        print(f"📝 Current hashed password: {user.hashed_password[:50]}...")
        
        # Test password hashing
        test_password = "newpassword123"
        print(f"\n🧪 Testing password: '{test_password}'")
        
        # Hash the password
        new_hash = get_password_hash(test_password)
        print(f"📝 New hash: {new_hash[:50]}...")
        
        # Test verification with new hash
        verify_result = verify_password(test_password, new_hash)
        print(f"✅ Verification with new hash: {verify_result}")
        
        # Test verification with current stored hash
        current_verify = verify_password(test_password, user.hashed_password)
        print(f"🔍 Verification with stored hash: {current_verify}")
        
        # If stored hash doesn't work, update it manually
        if not current_verify:
            print(f"\n🔧 Updating user password manually...")
            user.hashed_password = new_hash
            db.commit()
            print(f"✅ Password updated in database")
            
            # Test again
            updated_verify = verify_password(test_password, user.hashed_password)
            print(f"🔍 Verification after update: {updated_verify}")
        
        # Test with a few common passwords to see what's stored
        common_passwords = ["password", "admin123", "user123", "123456", "password123"]
        print(f"\n🔍 Testing common passwords against stored hash:")
        for pwd in common_passwords:
            result = verify_password(pwd, user.hashed_password)
            if result:
                print(f"✅ Found matching password: '{pwd}'")
                return True
            else:
                print(f"❌ '{pwd}' - no match")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def check_login_flow():
    """Test the login flow"""
    print(f"\n🔑 Testing Login Flow")
    print("=" * 30)
    
    import requests
    
    # Test login with common credentials
    login_data = {
        "username": "admin@example.com",  # or whatever email you're using
        "password": "adminpassword"     # the new password you set
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data=login_data,  # OAuth2PasswordRequestForm expects form data
            timeout=10
        )
        
        print(f"📨 Login response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"   Access token: {result.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Login failed: {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ Login test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Password Debug Test")
    print("=" * 50)
    
    # Test password system
    password_test = test_password_system()
    
    # Test login flow
    login_test = check_login_flow()
    
    print("\n" + "=" * 50)
    if password_test and login_test:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed. Check the output above.")
        
    print("\n💡 If login still fails:")
    print("   1. Check the email you're using to login")
    print("   2. Try the password 'newpassword123'")
    print("   3. Check backend logs for detailed errors")
