from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.db.database import get_mongo_collection
from app.schemas.review import ReviewBase, ReviewInDB
from app.services.sentiment_analysis import SentimentAnalyzer
from sqlalchemy.orm import Session
from app.db.database import get_postgres_db
from app.db import postgres_models as models

router = APIRouter()

@router.post("/", response_model=ReviewInDB)
async def create_review(review: ReviewBase, db: Session = Depends(get_postgres_db)):
    collection = get_mongo_collection("reviews")
    
    # Prevent shop owners from reviewing their own shops
    shop = db.query(models.Shop).filter(models.Shop.id == review.shopId).first()
    if shop and shop.owner_user_id == review.userId:
        raise HTTPException(status_code=403, detail="Shop owners cannot review their own shops")
    
    # Check if review already exists
    existing = await collection.find_one({
        "shopId": review.shopId,
        "userId": review.userId
    })
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="You've already reviewed this shop"
        )
    
    # Analyze sentiment if comment exists
    if review.comment:
        # Initialize sentiment analyzer
        analyzer = SentimentAnalyzer()
        
        # Get sentiment analysis results
        sentiment_results = analyzer.analyze_sentiment(review.comment)
        
        # Add sentiment data to review
        review.sentiment_score = sentiment_results.get("polarity_score", 0.0)
        review.sentiment_label = sentiment_results.get("overall_sentiment", "neutral")
        review.sentiment_details = sentiment_results
    
    result = await collection.insert_one(review.model_dump())
    created_review = await collection.find_one({"_id": result.inserted_id})
    return ReviewInDB.from_mongo(created_review)

@router.get("/", response_model=List[ReviewInDB])
async def read_reviews(skip: int = 0, limit: int = 100):
    collection = get_mongo_collection("reviews")
    reviews = await collection.find().skip(skip).limit(limit).to_list(length=limit)
    
    # Process reviews to add sentiment analysis if missing
    analyzer = SentimentAnalyzer()
    processed_reviews = []
    
    for review in reviews:
        review_obj = ReviewInDB.from_mongo(review)
        
        # Add sentiment analysis if not already present and comment exists
        if not hasattr(review_obj, 'sentiment_score') and review_obj.comment:
            sentiment_results = analyzer.analyze_sentiment(review_obj.comment)
            review_obj.sentiment_score = sentiment_results.get("polarity_score", 0.0)
            review_obj.sentiment_label = sentiment_results.get("overall_sentiment", "neutral")
            review_obj.sentiment_details = sentiment_results
            
            # Update the review in the database with sentiment data
            await collection.update_one(
                {"_id": review["_id"]},
                {"$set": {
                    "sentiment_score": review_obj.sentiment_score,
                    "sentiment_label": review_obj.sentiment_label,
                    "sentiment_details": review_obj.sentiment_details
                }}
            )
        
        processed_reviews.append(review_obj)
    
    return processed_reviews

@router.get("/shop/{shop_id}", response_model=List[ReviewInDB])
async def read_shop_reviews(shop_id: int, skip: int = 0, limit: int = 100):
    collection = get_mongo_collection("reviews")
    reviews = await collection.find({"shopId": shop_id}).skip(skip).limit(limit).to_list(length=limit)
    
    # Process reviews to add sentiment analysis if missing
    analyzer = SentimentAnalyzer()
    processed_reviews = []
    
    for review in reviews:
        review_obj = ReviewInDB.from_mongo(review)
        
        # Add sentiment analysis if not already present and comment exists
        if not hasattr(review_obj, 'sentiment_score') and review_obj.comment:
            sentiment_results = analyzer.analyze_sentiment(review_obj.comment)
            review_obj.sentiment_score = sentiment_results.get("polarity_score", 0.0)
            review_obj.sentiment_label = sentiment_results.get("overall_sentiment", "neutral")
            review_obj.sentiment_details = sentiment_results
            
            # Update the review in the database with sentiment data
            await collection.update_one(
                {"_id": review["_id"]},
                {"$set": {
                    "sentiment_score": review_obj.sentiment_score,
                    "sentiment_label": review_obj.sentiment_label,
                    "sentiment_details": review_obj.sentiment_details
                }}
            )
        
        processed_reviews.append(review_obj)
    
    return processed_reviews

# Utility endpoint used by the frontend to determine if a user owns a shop
@router.get("/check-ownership/{shop_id}/{user_id}")
def check_shop_ownership(shop_id: int, user_id: int, db: Session = Depends(get_postgres_db)):
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        return {"isOwner": False}
    return {"isOwner": shop.owner_user_id == user_id}