#!/usr/bin/env python3
"""
Quick test of the broadcast API without authentication
"""

import requests
import json

def test_broadcast_api():
    """Test the broadcast API endpoint"""
    
    url = "http://localhost:8000/api/notifications/broadcast"
    
    test_data = {
        "title": "Quick Test Announcement",
        "message": "This is a test to verify the API works without authentication errors."
    }
    
    print(f"🧪 Testing: {url}")
    print(f"📋 Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"📨 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Failed!")
            try:
                error = response.json()
                print(f"📄 Error: {json.dumps(error, indent=2)}")
            except:
                print(f"📄 Raw error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server!")
        print(f"🔧 Start server: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick API Test")
    print("=" * 30)
    test_broadcast_api()
