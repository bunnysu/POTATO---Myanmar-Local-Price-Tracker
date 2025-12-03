from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_postgres_db
from app.schemas.shop import ShopCreate, ShopInDB, ShopResponse, ShopUpdate
from app.db import postgres_models as models
from app.core.security import get_current_user
from app.schemas.user import UserInDB

router = APIRouter()

@router.post("/", response_model=ShopResponse)
def create_shop(
    shop: ShopCreate, 
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user)
):
    # Check if user is a retailer
    if current_user.role not in [models.UserRole.RETAILER, models.UserRole.USER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only retailers can create shops"
        )
    
    # Check if township exists if provided
    if shop.township_id:
        db_township = db.query(models.Township).filter(models.Township.id == shop.township_id).first()
        if not db_township:
            raise HTTPException(status_code=404, detail="Township not found")
    
    # Check if region exists if provided
    if shop.region_id:
        db_region = db.query(models.Region).filter(models.Region.id == shop.region_id).first()
        if not db_region:
            raise HTTPException(status_code=404, detail="Region not found")

    db_shop = models.Shop(
        shop_name=shop.shop_name,
        address_text=shop.address_text,
        operating_hours=shop.operating_hours,
        phone_number=shop.phone_number,
        status=models.ShopStatus.UNVERIFIED,
        owner_user_id=current_user.id,
        region_id=shop.region_id,
        township_id=shop.township_id
    )
    
    try:
        db.add(db_shop)
        db.commit()
        db.refresh(db_shop)
        return db_shop
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shop"
        )

@router.get("/", response_model=list[ShopResponse])
def read_shops(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_postgres_db)
):
    shops = db.query(models.Shop).offset(skip).limit(limit).all()
    return shops

@router.get("/owner/{owner_user_id}", response_model=list[ShopResponse])
def read_shops_by_owner(owner_user_id: int, db: Session = Depends(get_postgres_db)):
    shops = db.query(models.Shop).filter(models.Shop.owner_user_id == owner_user_id).all()
    return shops

@router.get("/{shop_id}", response_model=ShopResponse)
def read_shop(shop_id: int, db: Session = Depends(get_postgres_db)):
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

@router.put("/{shop_id}", response_model=ShopResponse)
def update_shop(
    shop_id: int,
    shop_update: ShopUpdate,
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user)
):
    # Get the shop
    db_shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not db_shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Check if user owns this shop or is admin
    if db_shop.owner_user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own shops"
        )
    
    # Update fields if provided
    if shop_update.shop_name is not None:
        db_shop.shop_name = shop_update.shop_name
    if shop_update.address_text is not None:
        db_shop.address_text = shop_update.address_text
    if shop_update.operating_hours is not None:
        db_shop.operating_hours = shop_update.operating_hours
    if shop_update.phone_number is not None:
        db_shop.phone_number = shop_update.phone_number
    if shop_update.region_id is not None:
        db_shop.region_id = shop_update.region_id
    if shop_update.township_id is not None:
        db_shop.township_id = shop_update.township_id
    if shop_update.status is not None:
        db_shop.status = shop_update.status
    if shop_update.image_url is not None:
        db_shop.image_url = shop_update.image_url
    
    try:
        db.add(db_shop)
        db.commit()
        db.refresh(db_shop)
        return db_shop
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update shop"
        )

@router.get("/{shop_id}/rating")
async def get_shop_rating(shop_id: int):
    """Get shop rating and review count from MongoDB"""
    try:
        from app.db.database import get_mongo_collection
        
        # Get reviews collection
        reviews_collection = get_mongo_collection("reviews")
        
        # Find all reviews for this shop
        reviews = await reviews_collection.find({"shopId": shop_id}).to_list(length=1000)
        
        if not reviews:
            return {
                "average_rating": 0,
                "total_reviews": 0,
                "rating_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            }
        
        # Calculate average rating
        total_rating = sum(review.get("rating", 0) for review in reviews)
        average_rating = round(total_rating / len(reviews), 1)
        
        # Calculate rating breakdown
        rating_breakdown = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for review in reviews:
            rating = review.get("rating", 0)
            if rating in rating_breakdown:
                rating_breakdown[str(rating)] += 1
        
        return {
            "average_rating": average_rating,
            "total_reviews": len(reviews),
            "rating_breakdown": rating_breakdown
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shop rating: {str(e)}"
        )

@router.get("/{shop_id}/reviews")
async def get_shop_reviews(shop_id: int, skip: int = 0, limit: int = 10):
    """Get shop reviews from MongoDB with pagination and user details"""
    try:
        from app.db.database import get_mongo_collection, get_postgres_db
        from sqlalchemy.orm import Session
        
        # Get reviews collection
        reviews_collection = get_mongo_collection("reviews")
        
        # Find reviews for this shop with pagination
        reviews = await reviews_collection.find({"shopId": shop_id}).skip(skip).limit(limit).to_list(length=limit)
        
        # Get PostgreSQL database session for user details
        db = next(get_postgres_db())
        
        try:
            # Enhance reviews with user information
            enhanced_reviews = []
            for review in reviews:
                # Convert ObjectId to string for JSON serialization
                if "_id" in review:
                    review["_id"] = str(review["_id"])
                
                # Get user details from PostgreSQL
                user_id = review.get("userId")
                if user_id:
                    try:
                        from app.db import postgres_models as models
                        db_user = db.query(models.User).filter(models.User.id == user_id).first()
                        if db_user:
                            review["user_name"] = db_user.full_name
                            review["user_role"] = db_user.role.value if hasattr(db_user.role, 'value') else str(db_user.role)
                            review["user_email"] = db_user.email
                        else:
                            review["user_name"] = "Unknown User"
                            review["user_role"] = "Customer"
                    except Exception as user_error:
                        print(f"Error fetching user {user_id}: {user_error}")
                        review["user_name"] = "Unknown User"
                        review["user_role"] = "Customer"
                else:
                    review["user_name"] = "Anonymous User"
                    review["user_role"] = "Customer"
                
                enhanced_reviews.append(review)
            
            return enhanced_reviews
            
        finally:
            db.close()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shop reviews: {str(e)}"
        )

