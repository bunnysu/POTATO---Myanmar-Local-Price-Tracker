from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.database import get_mongo_collection, get_postgres_db
from app.schemas.price_entry import PriceEntryBase, PriceEntryInDB
from app.db import postgres_models as models
from app.core.security import get_current_user
from app.schemas.user import UserInDB
from bson import ObjectId
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def convert_mongo_doc_to_json(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return doc
    
    # Convert ObjectId to string
    if '_id' in doc and isinstance(doc['_id'], ObjectId):
        doc['_id'] = str(doc['_id'])
    
    # Handle nested documents
    for key, value in doc.items():
        if isinstance(value, dict):
            doc[key] = convert_mongo_doc_to_json(value)
        elif isinstance(value, list):
            doc[key] = [convert_mongo_doc_to_json(item) if isinstance(item, dict) else item for item in value]
    
    return doc

async def create_price_alerts_for_favorites(db: Session, shop_id: int, item_id: int, price: float, price_type: str, shop_name: str = None):
    """Create price alert notifications for users who have favorited this shop"""
    try:
        # Find all users who have favorited this shop
        favorite_users = db.query(models.FavWatch).filter(
            models.FavWatch.shop_id == shop_id
        ).all()
        
        # Get shop name if not provided
        if not shop_name and shop_id:
            shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
            shop_name = shop.shop_name if shop else f"Shop #{shop_id}"
        
        # Get item name
        item = db.query(models.Item).filter(models.Item.id == item_id).first()
        item_name = item.name if item else f"Item #{item_id}"
        
        # Create notifications for each user who favorited this shop
        for fav in favorite_users:
            try:
                notification = models.Notification(
                    user_id=fav.user_id,
                    title="Price Alert",
                    message=f"{item_name} price updated to {price} MMK at {shop_name}",
                    category=models.NotificationCategory.PRICE,
                    read=False
                )
                db.add(notification)
                logger.info(f"Created price alert for user {fav.user_id} - {item_name} at {shop_name}")
            except Exception as e:
                logger.error(f"Failed to create notification for user {fav.user_id}: {e}")
                continue
        
        db.commit()
        logger.info(f"Successfully created price alerts for {len(favorite_users)} users")
        
    except Exception as e:
        logger.error(f"Failed to create price alerts: {e}")
        db.rollback()

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

@router.post("/", response_model=PriceEntryInDB)
async def create_price_entry(
    price_entry: PriceEntryBase,
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user)
):
    # Check if the user is banned
    if current_user.status == models.UserStatus.BANNED:
        # Check if the ban has expired (1 month)
        one_month_ago = datetime.now(ZoneInfo("Asia/Yangon")) - timedelta(days=30)
        if current_user.updated_at and current_user.updated_at < one_month_ago:
            # Unban the user
            current_user.status = models.UserStatus.ACTIVE
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        else:
            # Ban is still active
            raise HTTPException(status_code=403, detail="You are currently banned and cannot add price entries.")

    # Check if user has permission to add prices
    if current_user.role not in [models.UserRole.CONTRIBUTOR, models.UserRole.RETAILER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only contributors, retailers, and admins can add price entries")
    
    # Derive location/submittedBy from shop when possible
    location = price_entry.location
    submitted_by = price_entry.submittedBy

    if price_entry.shopId is not None:
        shop = db.query(models.Shop).filter(models.Shop.id == price_entry.shopId).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        # Verify that the current user owns this shop or is an admin
        if shop.owner_user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="You can only add prices for your own shop")
        
        # If location is missing, derive from shop
        if location is None:
            location = {
                "region_id": shop.region_id,
                "township_id": shop.township_id,
            }
        # If submittedBy is missing, derive from shop owner
        if submitted_by is None:
            submitted_by = {
                "id": current_user.id,
                "role": str(current_user.role.value),
            }

    # If submittedBy was not provided, default to current user
    if submitted_by is None:
        submitted_by = {
            "id": current_user.id,
            "role": str(current_user.role.value),
        }

    # Validate we have location
    if location is None:
        raise HTTPException(status_code=400, detail="location is required (provide township_id or a valid shopId)")

    # Get township and region
    township_id = location["township_id"] if isinstance(location, dict) else location.township_id
    township = db.query(models.Township).filter(models.Township.id == township_id).first()
    if not township:
        raise HTTPException(status_code=404, detail="Township not found")

    # Resolve region: prefer provided region_id; else derive from township; if submittedBy provided and user has region_id, use that
    region_id = None
    if isinstance(location, dict):
        region_id = location.get("region_id")
    else:
        region_id = getattr(location, "region_id", None)

    if region_id is None:
        # Try from submitting user
        if submitted_by is not None:
            user_id = submitted_by["id"] if isinstance(submitted_by, dict) else submitted_by.id
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user and getattr(user, "region_id", None) is not None:
                region_id = user.region_id
        # Fallback to township
        if region_id is None:
            region_id = township.region_id

    region = db.query(models.Region).filter(models.Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    # Prepare document for MongoDB
    entry_data = price_entry.model_dump()
    logger.info(f"📝 Original price entry data: {entry_data}")
    
    # Ensure location contains both township_id and region_id
    location_dict = location if isinstance(location, dict) else location.model_dump()
    location_dict["region_id"] = region_id
    location_dict["township_id"] = township_id
    entry_data["location"] = location_dict
    
    if submitted_by is not None:
        entry_data["submittedBy"] = submitted_by if isinstance(submitted_by, dict) else submitted_by.model_dump()
    
    # Get shop name if shopId is provided
    shop_name = None
    if price_entry.shopId is not None:
        shop = db.query(models.Shop).filter(models.Shop.id == price_entry.shopId).first()
        if shop:
            shop_name = shop.shop_name
    
    entry_data.update({
        "region_name": region.name,
        "township_name": township.name,
        "coordinates": {"lat": township.latitude, "lng": township.longitude},
        "shop_name": shop_name,
    })
    
    logger.info(f"📝 Final MongoDB document: {entry_data}")

    try:
        collection = get_mongo_collection("price_entries")
        logger.info(f"📁 Got MongoDB collection: price_entries")
        
        # Test the collection connection
        collection_stats = await collection.estimated_document_count()
        logger.info(f"📊 Collection stats: {collection_stats} documents")
        
        # Insert the document
        logger.info("📤 Inserting document into MongoDB...")
        result = await collection.insert_one(entry_data)
        logger.info(f"✅ Document inserted successfully with ID: {result.inserted_id}")
        
        # Verify the document was inserted
        created_entry = await collection.find_one({"_id": result.inserted_id})
        if created_entry:
            logger.info(f"✅ Document verified in MongoDB: {created_entry}")
        else:
            logger.error("❌ Document not found after insertion!")
            
        # Create price alerts for users who have favorited this shop
        if price_entry.shopId is not None:
            await create_price_alerts_for_favorites(db, price_entry.shopId, price_entry.itemId, price_entry.price, price_entry.type)
        
        return PriceEntryInDB.from_mongo(created_entry)
        
    except Exception as mongo_error:
        logger.error(f"❌ MongoDB operation failed: {mongo_error}")
        logger.error(f"❌ Error type: {type(mongo_error)}")
        logger.error(f"❌ Error details: {str(mongo_error)}")
        raise HTTPException(status_code=500, detail=f"Failed to save to database: {str(mongo_error)}")

@router.get("/test-mongo", tags=["debug"])
async def test_mongodb():
    """Test MongoDB connection and show database contents"""
    try:
        collection = get_mongo_collection("price_entries")
        
        # Get collection stats
        doc_count = await collection.estimated_document_count()
        
        # Get a few sample documents and convert ObjectIds to strings
        sample_docs_raw = await collection.find().limit(5).to_list(length=5)
        sample_docs = [convert_mongo_doc_to_json(doc) for doc in sample_docs_raw]
        
        # Get all documents for shop ID 2 and convert ObjectIds
        shop_2_docs_raw = await collection.find({"shopId": 2}).to_list(length=10)
        shop_2_docs = [convert_mongo_doc_to_json(doc) for doc in shop_2_docs_raw]
        
        return {
            "status": "success",
            "collection": "price_entries",
            "total_documents": doc_count,
            "sample_documents": sample_docs,
            "shop_2_documents": shop_2_docs,
            "message": "MongoDB connection test successful"
        }
        
    except Exception as e:
        logger.error(f"❌ MongoDB test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "MongoDB connection test failed"
        }

@router.get("/shop/{shop_id}", response_model=List[PriceEntryInDB])
async def read_shop_price_entries(
    shop_id: int,
    db: Session = Depends(get_postgres_db)
):
    """Get all price entries for a specific shop"""
    try:
        # First verify the shop exists
        shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        # Get price entries from MongoDB for this shop
        collection = get_mongo_collection("price_entries")
        entries_raw = await collection.find({"shopId": shop_id}).to_list(length=1000)
        
        # Convert ObjectIds to strings for JSON serialization
        entries = [convert_mongo_doc_to_json(entry) for entry in entries_raw]

        # Force timestamps to Asia/Yangon for response; treat naive as UTC
        for entry in entries:
            ts = entry.get("timestamp")
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                entry["timestamp"] = ts.astimezone(ZoneInfo("Asia/Yangon"))
        
        # Enrich entries with shop name if not already present
        for entry in entries:
            if entry.get('shop_name') is None:
                entry['shop_name'] = shop.shop_name
        
        logger.info(f"✅ Found {len(entries)} price entries for shop {shop_id}")
        return [PriceEntryInDB.from_mongo(entry) for entry in entries]
        
    except Exception as e:
        logger.error(f"❌ Error reading shop price entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read price entries: {str(e)}")

@router.get("/contributor/{user_id}", response_model=List[PriceEntryInDB])
async def read_contributor_price_entries(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
):
    """Get all price entries submitted by a specific contributor (from MongoDB)."""
    try:
        collection = get_mongo_collection("price_entries")
        mongo_filter = {"submittedBy.id": user_id}
        cursor = collection.find(mongo_filter).sort([("timestamp", -1)])
        entries_raw = await cursor.skip(skip).limit(limit).to_list(length=1000)

        # Convert ObjectIds to strings for JSON serialization
        entries = [convert_mongo_doc_to_json(entry) for entry in entries_raw]

        # Force timestamps to Asia/Yangon for response; treat naive as UTC
        for entry in entries:
            ts = entry.get("timestamp")
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                entry["timestamp"] = ts.astimezone(ZoneInfo("Asia/Yangon"))
        return [PriceEntryInDB.from_mongo(entry) for entry in entries]
    except Exception as e:
        logger.error(f"❌ Error reading contributor price entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read contributor price entries: {str(e)}")

@router.get("/", response_model=List[PriceEntryInDB])
async def read_price_entries(
    skip: int = 0,
    limit: int = 100,
    category: Optional[int] = Query(default=None),
    item: Optional[int] = Query(default=None),
    region: Optional[int] = Query(default=None),
    township: Optional[int] = Query(default=None),
    sort: Optional[str] = Query(default=None),
    priceType: Optional[str] = Query(default=None),
    db: Session = Depends(get_postgres_db)
):
    logger.info(f"🔍 Prices API called with params: category={category}, item={item}, region={region}, township={township}, sort={sort}, priceType={priceType}")
    
    collection = get_mongo_collection("price_entries")

    mongo_filter: dict = {}
    if item is not None:
        mongo_filter["itemId"] = item
    if priceType is not None:
        # Frontend sends retail/wholesale, our schema uses uppercase
        mongo_filter["type"] = priceType.upper()
    # Prefer township as the authoritative geo filter. If township is present,
    # don't also filter by region to avoid dropping docs that lack region_id
    # (older entries) or have derived region mismatches.
    if township is not None:
        mongo_filter["location.township_id"] = township
    elif region is not None:
        # Include docs that either have region_id or have a township within the region
        township_ids = [t.id for t in db.query(models.Township).filter(models.Township.region_id == region).all()]
        if township_ids:
            mongo_filter["$or"] = [
                {"location.region_id": region},
                {"location.township_id": {"$in": township_ids}},
            ]
        else:
            mongo_filter["location.region_id"] = region

    # Handle category filtering by getting all items in the category from Postgres
    # then filtering MongoDB results by those item IDs
    if category is not None:
        logger.info(f"🔍 Filtering by category: {category}")
        # Get all items in this category from Postgres
        items_in_category = db.query(models.Item).filter(models.Item.category_id == category).all()
        item_ids = [item.id for item in items_in_category]
        logger.info(f"📋 Found {len(item_ids)} items in category {category}: {item_ids}")
        if item_ids:
            # If item is also specified, check if it's in the category
            if item is not None:
                if item not in item_ids:
                    logger.info(f"⚠️ Item {item} is not in category {category}, returning empty result")
                    return []
                # Item is in category, so we can use the item filter directly
                mongo_filter["itemId"] = item
            else:
                # No specific item, filter by all items in category
                mongo_filter["itemId"] = {"$in": item_ids}
            logger.info(f"🔍 MongoDB filter updated with itemIds: {item_ids}")
        else:
            # No items in this category, return empty result
            logger.info(f"⚠️ No items found in category {category}, returning empty result")
            return []

    sort_spec = None
    if sort == "recent":
        sort_spec = [("timestamp", -1)]
    elif sort == "last-7-days":
        # Filter last 7 days server-side
        since = datetime.now(ZoneInfo("Asia/Yangon")) - timedelta(days=7)
        mongo_filter["timestamp"] = {"$gte": since}
        sort_spec = [("timestamp", -1)]
    elif sort == "last-1-month":
        since = datetime.now(ZoneInfo("Asia/Yangon")) - timedelta(days=30)
        mongo_filter["timestamp"] = {"$gte": since}
        sort_spec = [("timestamp", -1)]

    logger.info(f"🔍 Final MongoDB filter: {mongo_filter}")
    
    cursor = collection.find(mongo_filter)
    if sort_spec:
        cursor = cursor.sort(sort_spec)
    entries_raw = await cursor.skip(skip).limit(limit).to_list(length=1000)
    
    logger.info(f"📊 Found {len(entries_raw)} price entries matching filter")
    
    # Convert ObjectIds to strings for JSON serialization
    entries = [convert_mongo_doc_to_json(entry) for entry in entries_raw]
    # Normalize timestamps to Asia/Yangon; assume UTC when naive
    for entry in entries:
        ts = entry.get('timestamp')
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            entry['timestamp'] = ts.astimezone(ZoneInfo('Asia/Yangon'))

    # Normalize timestamps to Asia/Yangon; treat naive as Asia/Yangon to avoid double shifting legacy data
    for entry in entries:
        ts = entry.get("timestamp")
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=ZoneInfo("Asia/Yangon"))
            entry["timestamp"] = ts.astimezone(ZoneInfo("Asia/Yangon"))
    
    # Enrich entries with shop names for those that don't have them
    shop_cache = {}  # Cache shop names to avoid repeated queries
    for entry in entries:
        if entry.get('shopId') is not None and entry.get('shop_name') is None:
            shop_id = entry['shopId']
            if shop_id not in shop_cache:
                shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
                shop_cache[shop_id] = shop.shop_name if shop else f"Shop #{shop_id}"
            entry['shop_name'] = shop_cache[shop_id]
    
    # Log sample of returned items for debugging
    if entries:
        sample_items = entries[:3]  # Show first 3 entries
        logger.info(f"📊 Sample entries: {[{'itemId': e.get('itemId'), 'shop_name': e.get('shop_name', 'N/A')} for e in sample_items]}")
    
    result = [PriceEntryInDB.from_mongo(entry) for entry in entries]
    logger.info(f"✅ Returning {len(result)} price entries to frontend")
    return result

@router.put("/{price_entry_id}", response_model=PriceEntryInDB)
async def update_price_entry(
    price_entry_id: str,
    price_data: dict,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_postgres_db)
):
    """Update a price entry - only the owner can update their own entries"""
    logger.info(f"🔄 Updating price entry {price_entry_id} by user {current_user.id}")
    logger.info(f"📥 Received price_data: {price_data}")
    
    collection = get_mongo_collection("price_entries")
    
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(price_entry_id)
        except Exception as e:
            logger.error(f"❌ Invalid ObjectId format: {price_entry_id}, error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid price entry ID format: {price_entry_id}")
        
        # Find the price entry
        logger.info(f"🔍 Looking for entry with ObjectId: {object_id}")
        entry = await collection.find_one({"_id": object_id})
        if not entry:
            logger.error(f"❌ Price entry not found: {price_entry_id}")
            raise HTTPException(status_code=404, detail="Price entry not found")
        
        # Check if the current user is the owner of this entry
        if entry.get("submittedBy", {}).get("id") != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own price entries")
        
        # Validate the update data
        allowed_fields = {"price", "unit", "type", "itemId", "categoryId", "townshipId"}
        update_data = {k: v for k, v in price_data.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Validate price
        if "price" in update_data:
            try:
                price = float(update_data["price"])
                if price <= 0:
                    raise ValueError("Price must be positive")
                update_data["price"] = price
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid price value")
        
        # Validate type
        if "type" in update_data:
            if update_data["type"] not in ["WHOLESALE", "RETAIL"]:
                raise HTTPException(status_code=400, detail="Type must be WHOLESALE or RETAIL")
        
        # Validate unit
        if "unit" in update_data:
            if not update_data["unit"] or not update_data["unit"].strip():
                raise HTTPException(status_code=400, detail="Unit cannot be empty")
            update_data["unit"] = update_data["unit"].strip()

        # Validate itemId
        if "itemId" in update_data:
            try:
                item_id = int(update_data["itemId"])
                item = db.query(models.Item).filter(models.Item.id == item_id).first()
                if not item:
                    raise HTTPException(status_code=400, detail="Invalid item ID")
                update_data["itemId"] = item_id
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid item ID")

        # Validate categoryId (not stored in MongoDB but used for validation)
        if "categoryId" in update_data:
            try:
                category_id = int(update_data["categoryId"])
                category = db.query(models.Category).filter(models.Category.id == category_id).first()
                if not category:
                    raise HTTPException(status_code=400, detail="Invalid category ID")
                # Don't store categoryId in MongoDB as it's derived from itemId
                del update_data["categoryId"]
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid category ID")

        # Validate townshipId and update location
        if "townshipId" in update_data:
            try:
                township_id = int(update_data["townshipId"])
                township = db.query(models.Township).filter(models.Township.id == township_id).first()
                if not township:
                    raise HTTPException(status_code=400, detail="Invalid township ID")
                
                # Update location object
                update_data["location"] = {
                    "township_id": township_id,
                    "region_id": township.region_id
                }
                update_data["township_name"] = township.name
                
                # Get region name
                region = db.query(models.Region).filter(models.Region.id == township.region_id).first()
                if region:
                    update_data["region_name"] = region.name
                
                # Remove townshipId as we store it in location
                del update_data["townshipId"]
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid township ID")
        
        # Update the entry
        logger.info(f"📝 Updating entry with data: {update_data}")
        result = await collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        logger.info(f"📊 Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        
        if result.modified_count == 0:
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Price entry not found")
            else:
                raise HTTPException(status_code=400, detail="No changes were made - data is identical")
        
        # Get the updated entry
        updated_entry = await collection.find_one({"_id": object_id})
        if not updated_entry:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated entry")
            
        updated_entry = convert_mongo_doc_to_json(updated_entry)
        logger.info(f"✅ Entry updated successfully: {updated_entry.get('_id')}")
        
        logger.info(f"✅ Successfully updated price entry {price_entry_id}")
        return PriceEntryInDB.from_mongo(updated_entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating price entry {price_entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update price entry: {str(e)}")


@router.delete("/{price_entry_id}", response_model=dict)
async def delete_price_entry(
    price_entry_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_postgres_db)
):
    """Delete a price entry - only the owner can delete their own entries"""
    logger.info(f"🗑️ Deleting price entry {price_entry_id} by user {current_user.id}")
    
    collection = get_mongo_collection("price_entries")
    
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(price_entry_id)
        except Exception as e:
            logger.error(f"❌ Invalid ObjectId format: {price_entry_id}, error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid price entry ID format: {price_entry_id}")
        
        # Find the price entry
        logger.info(f"🔍 Looking for entry with ObjectId: {object_id}")
        entry = await collection.find_one({"_id": object_id})
        if not entry:
            logger.error(f"❌ Price entry not found: {price_entry_id}")
            raise HTTPException(status_code=404, detail="Price entry not found")
        
        # Check if the current user is the owner of this entry
        if entry.get("submittedBy", {}).get("id") != current_user.id:
            raise HTTPException(status_code=403, detail="You can only delete your own price entries")
        
        # Delete the entry
        logger.info(f"🗑️ Deleting entry with ObjectId: {object_id}")
        result = await collection.delete_one({"_id": object_id})
        
        logger.info(f"📊 Delete result - deleted: {result.deleted_count}")
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Price entry not found")
            
        logger.info(f"✅ Successfully deleted price entry {price_entry_id}")
        return {"message": "Price entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting price entry {price_entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete price entry: {str(e)}")
