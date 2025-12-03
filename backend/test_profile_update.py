#!/usr/bin/env python3
"""
Test script to verify profile update functionality
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv(dotenv_path='config.env')

def test_profile_update():
    """Test profile update functionality"""

    print("🔍 Testing Profile Update Functionality")
    print("=" * 50)

    # Backend URL
    base_url = "http://localhost:8000"
    
    # Test data
    test_user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "role": "CONTRIBUTOR"
    }

    try:
        # First, try to login to get a token
        print("🔐 Attempting to login...")
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print("Please make sure you have a test user with these credentials:")
            print(f"Email: {test_user_data['email']}")
            print(f"Password: {test_user_data['password']}")
            return

        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("❌ No access token received")
            return

        print("✅ Login successful")

        # Test the profile update endpoint
        print("\n📝 Testing profile update...")
        
        update_data = {
            "full_name": "Updated Test User",
            "phone_number": "+1234567890"
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        update_response = requests.put(
            f"{base_url}/api/users/me",
            json=update_data,
            headers=headers
        )

        if update_response.status_code == 200:
            updated_user = update_response.json()
            print("✅ Profile update successful!")
            print(f"Updated name: {updated_user.get('full_name')}")
            print(f"Updated phone: {updated_user.get('phone_number')}")
        else:
            print(f"❌ Profile update failed: {update_response.status_code}")
            print(f"Response: {update_response.text}")

        # Test getting the updated user data
        print("\n📖 Testing get current user...")
        me_response = requests.get(
            f"{base_url}/api/users/me",
            headers=headers
        )

        if me_response.status_code == 200:
            user_data = me_response.json()
            print("✅ Get current user successful!")
            print(f"Current name: {user_data.get('full_name')}")
            print(f"Current phone: {user_data.get('phone_number')}")
        else:
            print(f"❌ Get current user failed: {me_response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the backend server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_profile_update()
