#!/usr/bin/env python3
"""
Simple test script to verify the users endpoint is working
"""

import requests
import json

def test_users_endpoint():
    """Test the users endpoint"""
    base_url = "http://localhost:8000"
    
    try:
        # Test the users endpoint
        response = requests.get(f"{base_url}/api/users/")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Success! Found {len(users)} users:")
            for user in users:
                print(f"  - {user.get('full_name', 'N/A')} ({user.get('email', 'N/A')}) - {user.get('role', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure your backend server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Users Endpoint...")
    test_users_endpoint()
