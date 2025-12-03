import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from bson import ObjectId
from app.db.database import get_mongo_collection, SessionLocal
from app.db.postgres_models import User, Item, Shop, Category, UserRole, ShopStatus

async def test_reports():
    """Test script to check reports and create test data"""
    print("🔍 Testing Reports Database...")
    
    # Test MongoDB connection
    try:
        reports_collection = get_mongo_collection("reports")
        price_entries_collection = get_mongo_collection("price_entries")
        print("✅ MongoDB collections accessible")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return
    
    # Check existing reports
    try:
        all_reports = await reports_collection.find({}).to_list(length=100)
        print(f"📊 Found {len(all_reports)} total reports in database")
        
        pending_reports = await reports_collection.find({"status": "PENDING"}).to_list(length=100)
        print(f"⏳ Found {len(pending_reports)} pending reports")
        
        if pending_reports:
            print("📋 Pending reports details:")
            for report in pending_reports:
                print(f"  - ID: {report['_id']}, Status: {report['status']}, Details: {report['details']}")
        else:
            print("⚠️  No pending reports found!")
            
    except Exception as e:
        print(f"❌ Error checking reports: {e}")
        return
    
    # Check price entries
    try:
        all_price_entries = await price_entries_collection.find({}).to_list(length=100)
        print(f"💰 Found {len(all_price_entries)} price entries in database")
    except Exception as e:
        print(f"❌ Error checking price entries: {e}")
        return
    
    # If no pending reports, create some test data
    if len(pending_reports) == 0:
        print("\n🔄 Creating test reports...")
        
        # Create PostgreSQL session
        db = SessionLocal()
        
        try:
            # Ensure we have basic data
            category = Category(id=1, name="Grains")
            db.merge(category)
            
            user = User(id=1, full_name="Test User", email="test@example.com", 
                       hashed_password="dummy", role=UserRole.USER)
            db.merge(user)
            
            item = Item(id=1, name="Test Rice", default_unit="kg", category_id=1)
            db.merge(item)
            
            shop = Shop(id=1, shop_name="Test Shop", address_text="Test Location", 
                       owner_user_id=1, status=ShopStatus.VERIFIED)
            db.merge(shop)
            
            db.commit()
            print("✅ Created PostgreSQL test data")
            
            # Create a test price entry
            price_entry_id = ObjectId()
            price_entry = {
                "_id": price_entry_id,
                "itemId": 1,
                "type": "RETAIL",
                "price": 5000.0,
                "unit": "kg",
                "shopId": 1,
                "submittedBy": {"id": 1, "role": "USER"},
                "timestamp": datetime.now(ZoneInfo("Asia/Yangon")),
                "township_name": "Test Township"
            }
            
            await price_entries_collection.insert_one(price_entry)
            print("✅ Created test price entry")
            
            # Create a test pending report
            test_report = {
                "priceEntryId": price_entry_id,
                "reportedByUserId": 1,
                "reasonForFlag": "USER_SUGGESTION",
                "details": "User suggested price is 4500 kg. Reason: This seems too high",
                "status": "PENDING",
                "timestamp": datetime.now(ZoneInfo("Asia/Yangon"))
            }
            
            result = await reports_collection.insert_one(test_report)
            print(f"✅ Created test pending report with ID: {result.inserted_id}")
            
            # Verify the report was created
            new_pending_reports = await reports_collection.find({"status": "PENDING"}).to_list(length=100)
            print(f"📊 Now have {len(new_pending_reports)} pending reports")
            
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(test_reports())
