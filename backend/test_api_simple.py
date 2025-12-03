import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

def test_api():
    """Test the reports API endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("🔍 Testing Reports API...")
    
    # Test the pending reports endpoint
    try:
        response = requests.get(f"{base_url}/reports/queue/pending")
        print(f"📊 Pending reports endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Found {len(data)} pending reports")
            
            if data:
                for report in data:
                    print(f"  - ID: {report.get('id', 'N/A')}")
                    print(f"    Status: {report.get('status', 'N/A')}")
                    print(f"    Details: {report.get('details', 'N/A')}")
                    print()
            else:
                print("⚠️  No pending reports found!")
                
                # Create a test report
                print("🔄 Creating test report...")
                test_report = {
                    "priceEntryId": "507f1f77bcf86cd799439011",  # Dummy ObjectId
                    "reportedByUserId": 1,
                    "reasonForFlag": "USER_SUGGESTION",
                    "details": "Test report - User suggested price is 4500 kg. Reason: This seems too high",
                    "status": "PENDING",
                    "timestamp": datetime.now(ZoneInfo("Asia/Yangon")).isoformat()
                }
                
                create_response = requests.post(f"{base_url}/reports/", json=test_report)
                print(f"📝 Create report status: {create_response.status_code}")
                
                if create_response.status_code == 200:
                    print("✅ Test report created successfully!")
                    
                    # Check again
                    response2 = requests.get(f"{base_url}/reports/queue/pending")
                    if response2.status_code == 200:
                        data2 = response2.json()
                        print(f"📊 Now have {len(data2)} pending reports")
                else:
                    print(f"❌ Failed to create report: {create_response.text}")
        else:
            print(f"❌ API error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    # Test the general reports endpoint
    try:
        response = requests.get(f"{base_url}/reports/")
        print(f"\n📊 General reports endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Found {len(data)} total reports")
        else:
            print(f"❌ API error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing general API: {e}")

if __name__ == "__main__":
    test_api()
