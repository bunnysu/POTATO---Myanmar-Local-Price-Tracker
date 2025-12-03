import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from bson import ObjectId
import random
from sqlalchemy.orm import Session

from app.db.database import get_mongo_collection, SessionLocal
from app.db.postgres_models import User, Item, Shop, Category, UserRole, ShopStatus

async def seed_reports():
    """Seed the database with sample report data for testing"""
    reports_collection = get_mongo_collection("reports")
    price_entries_collection = get_mongo_collection("price_entries")
    
    # Clear existing reports and price entries
    await reports_collection.delete_many({})
    await price_entries_collection.delete_many({})
    
    # Create PostgreSQL session
    db = SessionLocal()
    
    try:
        # Create sample category
        category = Category(id=1, name="Grains")
        db.merge(category)
        
        # Create sample users in PostgreSQL
        users = [
            User(id=1, full_name="Ko Aung Aung", email="aung@example.com", 
                 hashed_password="dummy", role=UserRole.RETAILER),
            User(id=2, full_name="Ma Thida", email="thida@example.com", 
                 hashed_password="dummy", role=UserRole.CONTRIBUTOR),
            User(id=101, full_name="U Kyaw", email="kyaw@example.com", 
                 hashed_password="dummy", role=UserRole.USER),
            User(id=102, full_name="Daw Mya", email="mya@example.com", 
                 hashed_password="dummy", role=UserRole.USER)
        ]
        
        for user in users:
            db.merge(user)
        
        # Create sample items in PostgreSQL
        items = [
            Item(id=1, name="Pawsan Hmwe Rice", default_unit="kg", category_id=1),
            Item(id=2, name="Onion", default_unit="kg", category_id=1),
            Item(id=3, name="Tomato", default_unit="kg", category_id=1)
        ]
        
        for item in items:
            db.merge(item)
        
        # Create sample shops in PostgreSQL
        shops = [
            Shop(id=1, shop_name="ABC Groceries", address_text="Shwe Bo", 
                 owner_user_id=1, status=ShopStatus.VERIFIED),
            Shop(id=2, shop_name="XYZ Market", address_text="Mandalay", 
                 owner_user_id=2, status=ShopStatus.VERIFIED)
        ]
        
        for shop in shops:
            db.merge(shop)
        
        db.commit()
        print("✅ Created PostgreSQL data: users, items, shops")
        
        # Create price entries in MongoDB with all required fields
        price_entries = []
        
        # Price entry 1 - for AI flag report
        price_entry_1_id = ObjectId()
        price_entry_1 = {
            "_id": price_entry_1_id,
            "itemId": 1,
            "type": "WHOLESALE",
            "price": 160.0,
            "unit": "MMK/kg",
            "shopId": 1,
            "submittedBy": {"id": 1, "role": "RETAILER"},
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")) - timedelta(hours=2),
            "township_name": "Shwe Bo"
        }
        price_entries.append(price_entry_1)
        
        # Price entry 2 - for user suggestion report
        price_entry_2_id = ObjectId()
        price_entry_2 = {
            "_id": price_entry_2_id,
            "itemId": 1,
            "type": "RETAIL",
            "price": 4100.0,
            "unit": "Kg",
            "shopId": 2,
            "submittedBy": {"id": 2, "role": "CONTRIBUTOR"},
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")) - timedelta(hours=1),
            "township_name": "Chan Aye Tharzan"
        }
        price_entries.append(price_entry_2)
        
        # Insert price entries into MongoDB
        await price_entries_collection.insert_many(price_entries)
        print("✅ Created MongoDB price entries")
        
        # Create reports linked to price entries in MongoDB
        sample_reports = []
        
        # AI Flag report
        ai_flag_report = {
            "priceEntryId": price_entry_1_id,
            "reportedByUserId": 1,  # System AI
            "reasonForFlag": "AI_FLAG_PRICE_HIGH",
            "details": "AI Flag: Price is 40% above average",
            "status": "PENDING",
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")) - timedelta(hours=1)
        }
        sample_reports.append(ai_flag_report)
        
        # User suggestion report
        user_report = {
            "priceEntryId": price_entry_2_id,
            "reportedByUserId": 101,
            "reasonForFlag": "USER_SUGGESTION",
            "details": "User suggested price is 3400 Kg. Reason: I think so",
            "status": "PENDING",
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")) - timedelta(minutes=30)
        }
        sample_reports.append(user_report)
        
        # Insert reports into MongoDB
        if sample_reports:
            result = await reports_collection.insert_many(sample_reports)
            print(f"✅ Created {len(result.inserted_ids)} MongoDB reports")
            
            # Print summary
            pending_count = len([r for r in sample_reports if r["status"] == "PENDING"])
            print(f"- {pending_count} pending reports")
            print("✅ Seed data creation completed successfully")
        else:
            print("❌ No reports to insert")
            
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_reports())
