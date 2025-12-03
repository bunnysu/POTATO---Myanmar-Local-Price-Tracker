#!/usr/bin/env python3
"""
Seed script to add sample reviews to MongoDB for testing
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Add the app directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv('config.env')

# MongoDB connection settings
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'price_tracker_db')

async def seed_reviews():
    """Seed the database with sample reviews"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    reviews_collection = db['reviews']
    
    print("🔌 Connected to MongoDB")
    print(f"📁 Using database: {MONGO_DB_NAME}")
    print(f"📝 Using collection: reviews")
    
    # First, let's check what users exist in PostgreSQL
    print("\n🔍 Checking existing users in PostgreSQL...")
    try:
        from app.db.database import get_postgres_db
        from app.db import postgres_models as models
        
        postgres_db = next(get_postgres_db())
        
        # Get existing users
        existing_users = postgres_db.query(models.User).all()
        print(f"📊 Found {len(existing_users)} users in PostgreSQL:")
        
        user_ids = []
        for user in existing_users:
            print(f"   - User ID: {user.id}, Name: {user.full_name}, Role: {user.role}")
            user_ids.append(user.id)
        
        postgres_db.close()
        
        if not user_ids:
            print("❌ No users found in PostgreSQL. Please create users first.")
            return
            
        # Use the first few user IDs for reviews
        review_user_ids = user_ids[:4] if len(user_ids) >= 4 else user_ids
        
    except Exception as e:
        print(f"❌ Error checking PostgreSQL users: {e}")
        print("⚠️ Using default user IDs (1, 2, 3, 4)")
        review_user_ids = [1, 2, 3, 4]
    
    # Sample review data with real user IDs
    sample_reviews = [
        {
            "shopId": 1,  # Assuming shop ID 1 exists
            "userId": review_user_ids[0] if len(review_user_ids) > 0 else 1,
            "rating": 5,
            "comment": "Excellent service and great prices! Highly recommended.",
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")),
            "item_name": "Fresh Vegetables",
            "price": 5000
        },
        {
            "shopId": 1,  # Assuming shop ID 1 exists
            "userId": review_user_ids[1] if len(review_user_ids) > 1 else 2,
            "rating": 4,
            "comment": "Good quality products, friendly staff. Will visit again.",
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")),
            "item_name": "Organic Fruits",
            "price": 8000
        },
        {
            "shopId": 1,  # Assuming shop ID 1 exists
            "userId": review_user_ids[2] if len(review_user_ids) > 2 else 3,
            "rating": 5,
            "comment": "Best prices in town! Very fresh produce.",
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")),
            "item_name": "Rice",
            "price": 12000
        },
        {
            "shopId": 1,  # Assuming shop ID 1 exists
            "userId": review_user_ids[3] if len(review_user_ids) > 3 else 4,
            "rating": 3,
            "comment": "Decent prices but could improve on variety.",
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")),
            "item_name": "Cooking Oil",
            "price": 3500
        }
    ]
    
    try:
        # Clear existing reviews for shop 1
        await reviews_collection.delete_many({"shopId": 1})
        print("🧹 Cleared existing reviews for shop 1")
        
        # Insert sample reviews
        result = await reviews_collection.insert_many(sample_reviews)
        print(f"✅ Inserted {len(result.inserted_ids)} sample reviews")
        
        # Verify the reviews were inserted
        count = await reviews_collection.count_documents({"shopId": 1})
        print(f"📊 Total reviews for shop 1: {count}")
        
        # Show sample review
        sample_review = await reviews_collection.find_one({"shopId": 1})
        if sample_review:
            print(f"📝 Sample review: {sample_review['comment'][:50]}...")
            print(f"   User ID: {sample_review['userId']}")
        
        print("🎉 Reviews seeding completed successfully!")
        print("💡 Note: User names and roles will be fetched from PostgreSQL when reviews are displayed")
        
    except Exception as e:
        print(f"❌ Error seeding reviews: {e}")
    finally:
        client.close()
        print("🔌 MongoDB connection closed")

if __name__ == "__main__":
    print("🌱 Starting reviews seeding...")
    asyncio.run(seed_reviews())
