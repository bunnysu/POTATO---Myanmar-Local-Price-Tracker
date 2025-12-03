from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(settings.POSTGRES_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB connection with proper authentication
mongo_client = None
mongo_db = None

def connect_mongodb():
    global mongo_client, mongo_db
    try:
        # First try with authentication
        mongo_uri = f"mongodb://{settings.MONGO_INITDB_ROOT_USERNAME}:{settings.MONGO_INITDB_ROOT_PASSWORD}@{settings.MONGO_SERVER}:{settings.MONGO_PORT}/admin"
        logger.info(f"🔌 Attempting MongoDB connection with auth: {mongo_uri}")
        
        mongo_client = AsyncIOMotorClient(mongo_uri)
        mongo_client.admin.command('ping')
        logger.info("✅ MongoDB connected successfully with authentication")
        
        mongo_db = mongo_client[settings.MONGO_DB_NAME]
        logger.info(f"✅ Using MongoDB database: {settings.MONGO_DB_NAME}")
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection with auth failed: {e}")
        # Fallback to local MongoDB without authentication
        try:
            mongo_uri = f"mongodb://{settings.MONGO_SERVER}:{settings.MONGO_PORT}"
            logger.info(f"🔌 Attempting MongoDB connection without auth: {mongo_uri}")
            
            mongo_client = AsyncIOMotorClient(mongo_uri)
            mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully (no auth)")
            
            mongo_db = mongo_client[settings.MONGO_DB_NAME]
            logger.info(f"✅ Using MongoDB database: {settings.MONGO_DB_NAME}")
            
        except Exception as e2:
            logger.error(f"❌ MongoDB fallback connection also failed: {e2}")
            mongo_client = None
            mongo_db = None
            raise Exception(f"Failed to connect to MongoDB: {e2}")

# Initialize MongoDB connection
try:
    connect_mongodb()
except Exception as e:
    logger.error(f"🚨 MongoDB initialization failed: {e}")

def get_postgres_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mongo_collection(collection_name: str):
    global mongo_db
    if mongo_db is None:
        logger.error("❌ MongoDB is not connected")
        # Try to reconnect
        try:
            connect_mongodb()
        except Exception as e:
            logger.error(f"❌ Failed to reconnect to MongoDB: {e}")
            raise Exception("MongoDB is not connected and reconnection failed")
    
    if mongo_db is None:
        raise Exception("MongoDB is not connected")
    
    collection = mongo_db[collection_name]
    logger.info(f"📁 Using MongoDB collection: {collection_name}")
    return collection

# Test MongoDB connection
async def test_mongodb_connection():
    try:
        collection = get_mongo_collection("test")
        await collection.insert_one({"test": "connection", "timestamp": "now"})
        await collection.delete_one({"test": "connection"})
        logger.info("✅ MongoDB connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection test failed: {e}")
        return False