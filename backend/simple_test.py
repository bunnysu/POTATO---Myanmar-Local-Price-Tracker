import asyncio
import motor.motor_asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfo

async def simple_test():
    """Simple test to check MongoDB directly"""
    print("🔍 Simple MongoDB Test...")
    
    try:
        # Try different MongoDB connection options
        try:
            # First try with authentication
            client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://admin:password@localhost:27017/admin")
            db = client["price_activity_log"]
            print("✅ Connected with authentication")
        except Exception as auth_error:
            print(f"❌ Auth failed: {auth_error}")
            # Try without authentication
            client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
            db = client["price_activity_log"]
            print("✅ Connected without authentication")
        
        # Test reports collection
        reports_collection = db["reports"]
        all_reports = await reports_collection.find({}).to_list(length=100)
        print(f"📊 Found {len(all_reports)} total reports")
        
        pending_reports = await reports_collection.find({"status": "PENDING"}).to_list(length=100)
        print(f"⏳ Found {len(pending_reports)} pending reports")
        
        if pending_reports:
            print("📋 Pending reports:")
            for report in pending_reports:
                print(f"  - ID: {report['_id']}")
                print(f"    Status: {report['status']}")
                print(f"    Details: {report['details']}")
                print(f"    Timestamp: {report['timestamp']}")
                print()
        else:
            print("⚠️  No pending reports found!")
            
            # Create a simple test report
            print("🔄 Creating a test pending report...")
            test_report = {
                "priceEntryId": "507f1f77bcf86cd799439011",  # Dummy ObjectId
                "reportedByUserId": 1,
                "reasonForFlag": "USER_SUGGESTION",
                "details": "Test report - User suggested price is 4500 kg. Reason: This seems too high",
                "status": "PENDING",
                "timestamp": datetime.now(ZoneInfo("Asia/Yangon"))
            }
            
            result = await reports_collection.insert_one(test_report)
            print(f"✅ Created test report with ID: {result.inserted_id}")
            
            # Check again
            new_pending = await reports_collection.find({"status": "PENDING"}).to_list(length=100)
            print(f"📊 Now have {len(new_pending)} pending reports")
        
        # Test price entries collection
        price_entries_collection = db["price_entries"]
        all_entries = await price_entries_collection.find({}).to_list(length=100)
        print(f"💰 Found {len(all_entries)} price entries")
        
        if not all_entries:
            print("🔄 Creating a test price entry...")
            test_entry = {
                "itemId": 1,
                "type": "RETAIL",
                "price": 5000.0,
                "unit": "kg",
                "shopId": 1,
                "submittedBy": {"id": 1, "role": "USER"},
                "timestamp": datetime.now(ZoneInfo("Asia/Yangon")),
                "township_name": "Test Township"
            }
            
            entry_result = await price_entries_collection.insert_one(test_entry)
            print(f"✅ Created test price entry with ID: {entry_result.inserted_id}")
            
            # Update the test report to use this price entry
            await reports_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"priceEntryId": entry_result.inserted_id}}
            )
            print("✅ Updated test report to reference the price entry")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(simple_test())
