#!/usr/bin/env python3
"""
Test the notifications broadcast API endpoint
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/notifications/broadcast"

def test_broadcast_api():
    """Test the broadcast notifications API endpoint"""
    
    print("🧪 Testing Notifications Broadcast API")
    print("=" * 40)
    
    # Test data
    test_data = {
        "title": "API Test Announcement",
        "message": "This is a test announcement sent via the API to verify the broadcast functionality works correctly."
    }
    
    print(f"📤 Sending POST request to: {API_URL}")
    print(f"📋 Payload: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make the API call
        response = requests.post(
            API_URL,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📨 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Success Response:")
            print(f"   {json.dumps(response_data, indent=2)}")
            
            # Verify we got expected fields
            if "notifications_created" in response_data:
                count = response_data["notifications_created"]
                print(f"\n🎉 API Test PASSED!")
                print(f"   Created {count} notifications in database")
                return True
            else:
                print(f"\n⚠️  Unexpected response format")
                return False
                
        elif response.status_code == 403:
            print(f"❌ Authentication Error (403):")
            print(f"   This means you need to be logged in as an admin")
            print(f"   The API requires admin authentication")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
        else:
            print(f"❌ API Error ({response.status_code}):")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error:")
        print(f"   Cannot connect to {API_URL}")
        print(f"   Make sure your backend server is running:")
        print(f"   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except:
        print("❌ Backend server is not running")
        print("   Start it with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False

if __name__ == "__main__":
    print("🚀 API Endpoint Test")
    print("=" * 40)
    
    # Check server first
    if not check_server_status():
        print("\n💡 Start your server first, then run this test again.")
        exit(1)
    
    # Test the API
    success = test_broadcast_api()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 API Test PASSED!")
        print("✅ Your notifications broadcast endpoint is working!")
    else:
        print("💥 API Test FAILED!")
        print("🔧 Check the errors above and fix them.")
        
    print("\n💡 If you get authentication errors:")
    print("   The API requires admin login. You might need to:")
    print("   1. Disable authentication temporarily for testing, OR")
    print("   2. Implement proper login flow in your frontend")
