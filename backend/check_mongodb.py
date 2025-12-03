#!/usr/bin/env python3
"""
Script to check MongoDB database contents and connection
"""
import asyncio
import motor.motor_asyncio
from datetime import datetime

# MongoDB connection settings (same as backend)
MONGO_URI = "mongodb://admin:password@localhost:27017/admin"
DB_NAME = "price_activity_log"
COLLECTION_NAME = "price_entries"

async def check_mongodb():
    try:
        print("🔌 Connecting to MongoDB...")
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Get database
        db = client[DB_NAME]
        print(f"📁 Using database: {DB_NAME}")
        
        # List all collections
        collections = await db.list_collection_names()
        print(f"📚 Collections in {DB_NAME}: {collections}")
        
        # Check price_entries collection
        if COLLECTION_NAME in collections:
            collection = db[COLLECTION_NAME]
            
            # Get document count
            doc_count = await collection.estimated_document_count()
            print(f"📊 Total documents in {COLLECTION_NAME}: {doc_count}")
            
            # Get sample documents
            sample_docs = await collection.find().limit(5).to_list(length=5)
            print(f"\n📝 Sample documents:")
            for i, doc in enumerate(sample_docs):
                print(f"\n--- Document {i+1} ---")
                for key, value in doc.items():
                    if key == '_id':
                        print(f"  {key}: {value}")
                    elif key == 'timestamp':
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {value}")
            
            # Check for shop ID 2 specifically
            shop_2_docs = await collection.find({"shopId": 2}).to_list(length=10)
            print(f"\n🏪 Documents with shopId: 2")
            print(f"  Found: {len(shop_2_docs)} documents")
            
            if shop_2_docs:
                for i, doc in enumerate(shop_2_docs):
                    print(f"\n  --- Shop 2 Document {i+1} ---")
                    print(f"    itemId: {doc.get('itemId')}")
                    print(f"    price: {doc.get('price')}")
                    print(f"    type: {doc.get('type')}")
                    print(f"    timestamp: {doc.get('timestamp')}")
            
        else:
            print(f"❌ Collection '{COLLECTION_NAME}' not found in {DB_NAME}")
        
        # Also check other databases
        print(f"\n🔍 Checking other databases...")
        all_dbs = await client.list_database_names()
        print(f"Available databases: {all_dbs}")
        
        # Check if price_activity_log exists and has data
        if "price_activity_log" in all_dbs:
            print(f"\n📁 Found price_activity_log database")
            price_db = client["price_activity_log"]
            price_collections = await price_db.list_collection_names()
            print(f"Collections in price_activity_log: {price_collections}")
            
            if "price_entries" in price_collections:
                price_collection = price_db["price_entries"]
                price_doc_count = await price_collection.estimated_document_count()
                print(f"Documents in price_activity_log.price_entries: {price_doc_count}")
                
                # Check for shop ID 2 in this database too
                price_shop_2_docs = await price_collection.find({"shopId": 2}).to_list(length=5)
                print(f"Documents with shopId: 2 in price_activity_log: {len(price_shop_2_docs)}")
        
        client.close()
        print("\n✅ MongoDB check completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_mongodb())
