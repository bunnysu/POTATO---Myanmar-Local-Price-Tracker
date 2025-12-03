from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.db.database import get_postgres_db, get_mongo_collection
from app.core.security import get_current_user
from app.schemas.user import UserInDB
from app.db import postgres_models as models
from app.schemas.fav_watch import FavWatchBase, FavWatchInDB


router = APIRouter()


@router.post("/", response_model=FavWatchInDB)
def create_fav_watch(
    payload: FavWatchBase,
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user),
):
    print(f"🔍 Creating favorite: item_id={payload.item_id}, shop_id={payload.shop_id}, user_id={current_user.id}")
    if not payload.item_id and not payload.shop_id:
        raise HTTPException(status_code=400, detail="Provide item_id or shop_id")
    
    # For wholesale prices, shop_id can be None but item_id must be provided
    if payload.item_id and payload.shop_id is None:
        print(f"🔍 Processing wholesale favorite for item {payload.item_id}")
    elif payload.item_id and payload.shop_id:
        print(f"🔍 Processing retail favorite for item {payload.item_id} and shop {payload.shop_id}")
    else:
        print(f"🔍 Processing shop-only favorite for shop {payload.shop_id}")

    # Prevent shop owners from favoriting their own shops
    if payload.shop_id:
        shop = db.query(models.Shop).filter(models.Shop.id == payload.shop_id).first()
        if shop and shop.owner_user_id == current_user.id:
            raise HTTPException(status_code=403, detail="You cannot favorite your own shop")

    # Prevent duplicates
    query = db.query(models.FavWatch).filter(models.FavWatch.user_id == current_user.id)
    if payload.item_id:
        query = query.filter(models.FavWatch.item_id == payload.item_id)
    if payload.shop_id:
        query = query.filter(models.FavWatch.shop_id == payload.shop_id)
    else:
        # For wholesale prices (no shop_id), check if item is already favorited without shop
        query = query.filter(models.FavWatch.shop_id.is_(None))
    existing = query.first()
    if existing:
        print(f"⚠️ Duplicate favorite found: {existing.id}")
        return existing

    fav = models.FavWatch(user_id=current_user.id, item_id=payload.item_id, shop_id=payload.shop_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    print(f"✅ Favorite created successfully: {fav.id}")
    return fav


@router.get("/", response_model=List[FavWatchInDB])
async def list_fav_watch(
    price_type: Optional[str] = Query(default=None, description="Filter by price type: retail or wholesale"),
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Get user's favorites with detailed item and shop information"""
    favorites = db.query(models.FavWatch).filter(models.FavWatch.user_id == current_user.id).all()
    
    # Get price collection for fetching current prices
    price_collection = get_mongo_collection("price_entries")
    
    # Add additional information for frontend display
    result = []
    for fav in favorites:
        fav_dict = {
            "id": fav.id,
            "user_id": fav.user_id,
            "item_id": fav.item_id,
            "shop_id": fav.shop_id,
            "created_at": fav.created_at,
            "item_name": None,
            "shop_name": None,
            "item_unit": None,
            "shop_location": None,
            "current_prices": {
                "retail": {
                    "price": None,
                    "unit": None,
                    "item_name": None,
                    "timestamp": None
                },
                "wholesale": {
                    "price": None,
                    "unit": None,
                    "item_name": None,
                    "timestamp": None
                }
            }
        }
        
        # Get item details if item_id exists
        if fav.item_id:
            item = db.query(models.Item).filter(models.Item.id == fav.item_id).first()
            if item:
                fav_dict["item_name"] = item.name
                fav_dict["item_unit"] = item.default_unit
        
        # Get shop details if shop_id exists
        if fav.shop_id:
            shop = db.query(models.Shop).options(joinedload(models.Shop.region), joinedload(models.Shop.township)).filter(models.Shop.id == fav.shop_id).first()
            if shop:
                fav_dict["shop_name"] = shop.shop_name
                if shop.township and shop.region:
                    fav_dict["shop_location"] = f"{shop.township.name}, {shop.region.name}"
        
        # Get current prices from MongoDB
        if fav.item_id:
            # Get latest retail price
            retail_price = await price_collection.find_one(
                {"itemId": fav.item_id, "type": "RETAIL"},
                sort=[("timestamp", -1)]
            )
            if retail_price:
                fav_dict["current_prices"]["retail"] = {
                    "price": retail_price.get("price"),
                    "unit": retail_price.get("unit"),
                    "shop_name": retail_price.get("shop_name", f"Shop #{retail_price.get('shopId')}"),
                    "timestamp": retail_price.get("timestamp")
                }
            
            # Get latest wholesale price
            wholesale_price = await price_collection.find_one(
                {"itemId": fav.item_id, "type": "WHOLESALE"},
                sort=[("timestamp", -1)]
            )
            if wholesale_price:
                fav_dict["current_prices"]["wholesale"] = {
                    "price": wholesale_price.get("price"),
                    "unit": wholesale_price.get("unit"),
                    "shop_name": wholesale_price.get("shop_name", f"Shop #{wholesale_price.get('shopId')}"),
                    "timestamp": wholesale_price.get("timestamp")
                }
        
        elif fav.shop_id:
            # For shop favorites, get latest prices from that shop
            shop_prices = await price_collection.find(
                {"shopId": fav.shop_id},
                sort=[("timestamp", -1)]
            ).limit(10).to_list(length=10)
            
            retail_prices = [p for p in shop_prices if p.get("type") == "RETAIL"]
            wholesale_prices = [p for p in shop_prices if p.get("type") == "WHOLESALE"]
            
            if retail_prices:
                latest_retail = retail_prices[0]
                fav_dict["current_prices"]["retail"] = {
                    "price": latest_retail.get("price"),
                    "unit": latest_retail.get("unit"),
                    "item_name": None,  # Initialize the key
                    "timestamp": latest_retail.get("timestamp")
                }
                # Get item name from postgres
                if latest_retail.get("itemId"):
                    item = db.query(models.Item).filter(models.Item.id == latest_retail["itemId"]).first()
                    if item:
                        fav_dict["current_prices"]["retail"]["item_name"] = item.name
            
            if wholesale_prices:
                latest_wholesale = wholesale_prices[0]
                fav_dict["current_prices"]["wholesale"] = {
                    "price": latest_wholesale.get("price"),
                    "unit": latest_wholesale.get("unit"),
                    "item_name": None,  # Initialize the key
                    "timestamp": latest_wholesale.get("timestamp")
                }
                # Get item name from postgres
                if latest_wholesale.get("itemId"):
                    item = db.query(models.Item).filter(models.Item.id == latest_wholesale["itemId"]).first()
                    if item:
                        fav_dict["current_prices"]["wholesale"]["item_name"] = item.name
        
        # Apply price_type filter if specified
        if price_type:
            price_type_lower = price_type.lower()
            if price_type_lower == "retail" and not fav_dict["current_prices"]["retail"]["price"]:
                continue  # Skip this favorite if no retail price and filtering for retail
            elif price_type_lower == "wholesale" and not fav_dict["current_prices"]["wholesale"]["price"]:
                continue  # Skip this favorite if no wholesale price and filtering for wholesale
        
        result.append(fav_dict)
    
    return result


@router.delete("/{fav_id}")
def delete_fav_watch(
    fav_id: int,
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user),
):
    fav = db.query(models.FavWatch).filter(models.FavWatch.id == fav_id, models.FavWatch.user_id == current_user.id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return {"ok": True}
