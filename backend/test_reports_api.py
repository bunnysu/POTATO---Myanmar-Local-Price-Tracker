#!/usr/bin/env python3
"""
Test script to verify reports API and database connectivity
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add the app directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv('config.env')

# MongoDB connection settings
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'price_tracker_db')

async def test_reports_api():
    """Test the reports API and database connectivity"""
    
    print("🔍 Testing Reports API and Database Connectivity...")
    
    # Test MongoDB connection
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        reports_collection = db['reports']
        price_entries_collection = db['price_entries']
        
        print("✅ Connected to MongoDB")
        
        # Check reports collection
        reports_count = await reports_collection.count_documents({})
        print(f"📊 Reports in database: {reports_count}")
        
        # Check price entries collection
        price_entries_count = await price_entries_collection.count_documents({})
        print(f"📊 Price entries in database: {price_entries_count}")
        
        # Get sample reports
        sample_reports = await reports_collection.find({}).limit(5).to_list(length=5)
        print(f"📝 Sample reports: {len(sample_reports)}")
        
        for i, report in enumerate(sample_reports):
            print(f"  Report {i+1}: {report.get('reasonForFlag', 'N/A')} - {report.get('status', 'N/A')}")
        
        # Test aggregation pipeline
        pipeline = [
            {"$match": {"status": "PENDING"}},
            {"$lookup": {
                "from": "price_entries",
                "localField": "priceEntryId",
                "foreignField": "_id",
                "as": "priceEntry"
            }},
            {"$unwind": {"path": "$priceEntry", "preserveNullAndEmptyArrays": True}}
        ]
        
        aggregated_reports = await reports_collection.aggregate(pipeline).to_list(length=10)
        print(f"🔗 Aggregated reports with price entries: {len(aggregated_reports)}")
        
        for i, report in enumerate(aggregated_reports):
            price_entry = report.get('priceEntry', {})
            print(f"  Aggregated {i+1}: {report.get('reasonForFlag', 'N/A')} - Price: {price_entry.get('price', 'N/A')}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")
        return False
    
    # Test PostgreSQL connection
    try:
        from app.db.database import SessionLocal
        from app.db.postgres_models import User, Item, Shop
        
        db = SessionLocal()
        
        # Check users
        users_count = db.query(User).count()
        print(f"👥 Users in PostgreSQL: {users_count}")
        
        # Check items
        items_count = db.query(Item).count()
        print(f"📦 Items in PostgreSQL: {items_count}")
        
        # Check shops
        shops_count = db.query(Shop).count()
        print(f"🏪 Shops in PostgreSQL: {shops_count}")
        
        # Get sample users
        sample_users = db.query(User).limit(3).all()
        print(f"👤 Sample users: {len(sample_users)}")
        for user in sample_users:
            print(f"  User: {user.full_name} ({user.email}) - Warnings: {user.warning_count}")
        
        db.close()
        print("✅ PostgreSQL test completed")
        
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False
    
    print("🎉 All tests completed successfully!")
    return True

if __name__ == "__main__":
    asyncio.run(test_reports_api())
