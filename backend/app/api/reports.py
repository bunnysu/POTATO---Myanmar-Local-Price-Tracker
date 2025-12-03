from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.db.database import get_mongo_collection, get_postgres_db
from app.db.postgres_models import User, Item, Shop, UserStatus, Notification, NotificationCategory
from app.schemas.report import ReportBase, ReportInDB

router = APIRouter()

@router.get("/test")
async def test_reports_endpoint():
    """Test endpoint to verify reports API is working"""
    return {"message": "Reports API is working", "status": "ok"}

async def enrich_reports_with_postgres_data(reports: List[dict], db: Session) -> List[dict]:
    """Enrich MongoDB reports with PostgreSQL data"""
    enriched_reports = []
    
    for report in reports:
        enriched_report = report.copy()
        
        # Get price entry data
        price_entry = report.get("priceEntry")
        if price_entry:
            # Fetch user data from PostgreSQL
            if "submittedBy" in price_entry and "id" in price_entry["submittedBy"]:
                user_id = price_entry["submittedBy"]["id"]
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    enriched_report["submitterName"] = user.full_name
                    enriched_report["submitterRole"] = price_entry["submittedBy"]["role"]
            
            # Fetch item data from PostgreSQL
            if "itemId" in price_entry:
                item_id = price_entry["itemId"]
                item = db.query(Item).filter(Item.id == item_id).first()
                if item:
                    enriched_report["itemName"] = item.name
            
            # Fetch shop data from PostgreSQL
            if "shopId" in price_entry:
                shop_id = price_entry["shopId"]
                shop = db.query(Shop).filter(Shop.id == shop_id).first()
                if shop:
                    enriched_report["shopName"] = shop.shop_name
                    enriched_report["shopAddress"] = shop.address_text
            
            # Add other price entry fields
            enriched_report["priceType"] = price_entry.get("type")
            enriched_report["submittedPrice"] = price_entry.get("price")
            enriched_report["priceUnit"] = price_entry.get("unit")
            enriched_report["submissionDate"] = price_entry.get("timestamp")
            enriched_report["location"] = price_entry.get("township_name")
        
        enriched_reports.append(enriched_report)
    
    return enriched_reports

@router.post("/", response_model=ReportInDB)
async def create_report(report: ReportBase, db: Session = Depends(get_postgres_db)):
    collection = get_mongo_collection("reports")
    
    # Convert priceEntryId from string to ObjectId
    try:
        report_dict = report.model_dump()
        report_dict["priceEntryId"] = ObjectId(report.priceEntryId)
    except:
        raise HTTPException(status_code=400, detail="Invalid priceEntryId format")
    
    result = await collection.insert_one(report_dict)
    created_report = await collection.find_one({"_id": result.inserted_id})
    
    # Get the price entry to find the user who submitted it
    price_entries_collection = get_mongo_collection("price_entries")
    price_entry = await price_entries_collection.find_one({"_id": report_dict["priceEntryId"]})
    
    if price_entry and "submittedBy" in price_entry:
        user_id = price_entry["submittedBy"]["id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Create notification for the user that their submission has been reported
            report_notification = Notification(
                user_id=user.id,
                title="Price Submission Reported",
                message="Your price submission has been reported and is under review by our team. We will investigate this matter.",
                category=NotificationCategory.SYSTEM,
                read=False
            )
            db.add(report_notification)
            db.commit()
    
    return ReportInDB.from_mongo(created_report)

@router.get("/", response_model=List[ReportInDB])
async def read_reports(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in details field"),
    reason: Optional[str] = Query(None, description="Filter by reason for flag"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priceType: Optional[str] = Query(None, description="Filter by price type: RETAIL or WHOLESALE"),
    db: Session = Depends(get_postgres_db)
):
    collection = get_mongo_collection("reports")
    
    # Build query filter
    query = {}
    
    if search:
        query["details"] = {"$regex": search, "$options": "i"}
    
    if reason:
        # Map frontend filter values to backend enum values
        reason_mapping = {
            "ai_flag_price_high": "AI_FLAG_PRICE_HIGH",
            "user_suggestion": "USER_SUGGESTION"
        }
        mapped_reason = reason_mapping.get(reason.lower(), reason.upper())
        query["reasonForFlag"] = mapped_reason
    
    if status:
        query["status"] = status.upper()
    
    # Simple MongoDB aggregation to join with price entries only
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "price_entries",
            "localField": "priceEntryId",
            "foreignField": "_id",
            "as": "priceEntry"
        }},
        {"$unwind": {"path": "$priceEntry", "preserveNullAndEmptyArrays": True}}
    ]
    
    # Add price type filter after lookup if specified
    if priceType:
        pipeline.append({"$match": {"priceEntry.type": priceType.upper()}})
    
    # Add skip and limit
    pipeline.extend([
        {"$skip": skip},
        {"$limit": limit}
    ])
    
    reports_cursor = collection.aggregate(pipeline)
    reports = await reports_cursor.to_list(length=limit)
    
    # Debug logging
    print(f"DEBUG: Found {len(reports)} reports from MongoDB")
    
    # Enrich with PostgreSQL data
    enriched_reports = await enrich_reports_with_postgres_data(reports, db)
    
    # Convert to ReportInDB format (normalize timestamps to Asia/Yangon)
    result = []
    for report in enriched_reports:
        ts = report.get("timestamp")
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            report["timestamp"] = ts.astimezone(ZoneInfo("Asia/Yangon"))
        report_dict = {
            "_id": report["_id"],
            "priceEntryId": str(report["priceEntryId"]),
            "reportedByUserId": report["reportedByUserId"],
            "reasonForFlag": report["reasonForFlag"],
            "details": report["details"],
            "status": report["status"],
            "timestamp": report["timestamp"],
            "priceType": report.get("priceType"),
            "itemName": report.get("itemName"),
            "shopName": report.get("shopName"),
            "shopAddress": report.get("shopAddress"),
            "submittedPrice": report.get("submittedPrice"),
            "priceUnit": report.get("priceUnit"),
            "submissionDate": report.get("submissionDate"),
            "submitterName": report.get("submitterName"),
            "submitterRole": report.get("submitterRole"),
            "location": report.get("location")
        }
        result.append(ReportInDB.from_mongo(report_dict))
    
    return result

@router.get("/queue/pending", response_model=List[ReportInDB])
async def get_pending_reports(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in details field"),
    reason: Optional[str] = Query(None, description="Filter by reason for flag"),
    priceType: Optional[str] = Query(None, description="Filter by price type: RETAIL or WHOLESALE"),
    db: Session = Depends(get_postgres_db)
):
    print(f"DEBUG: get_pending_reports called with skip={skip}, limit={limit}, search={search}, reason={reason}")
    collection = get_mongo_collection("reports")
    
    # Build query filter for pending reports
    query = {"status": "PENDING"}
    
    if search:
        query["details"] = {"$regex": search, "$options": "i"}
    
    if reason:
        reason_mapping = {
            "ai_flag_price_high": "AI_FLAG_PRICE_HIGH",
            "user_suggestion": "USER_SUGGESTION"
        }
        mapped_reason = reason_mapping.get(reason.lower(), reason.upper())
        query["reasonForFlag"] = mapped_reason
    
    print(f"DEBUG: get_pending_reports - Query: {query}")
    
    # Simple MongoDB aggregation to join with price entries only
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "price_entries",
            "localField": "priceEntryId",
            "foreignField": "_id",
            "as": "priceEntry"
        }},
        {"$unwind": {"path": "$priceEntry", "preserveNullAndEmptyArrays": True}}
    ]
    
    # Add price type filter after lookup if specified
    if priceType:
        pipeline.append({"$match": {"priceEntry.type": priceType.upper()}})
    
    # Add sort, skip and limit
    pipeline.extend([
        {"$sort": {"timestamp": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ])
    
    reports_cursor = collection.aggregate(pipeline)
    reports = await reports_cursor.to_list(length=limit)
    
    # Enrich with PostgreSQL data
    enriched_reports = await enrich_reports_with_postgres_data(reports, db)
    
    # Convert to ReportInDB format (normalize timestamps to Asia/Yangon)
    result = []
    for report in enriched_reports:
        ts = report.get("timestamp")
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            report["timestamp"] = ts.astimezone(ZoneInfo("Asia/Yangon"))
        report_dict = {
            "_id": report["_id"],
            "priceEntryId": str(report["priceEntryId"]),
            "reportedByUserId": report["reportedByUserId"],
            "reasonForFlag": report["reasonForFlag"],
            "details": report["details"],
            "status": report["status"],
            "timestamp": report["timestamp"],
            "priceType": report.get("priceType"),
            "itemName": report.get("itemName"),
            "shopName": report.get("shopName"),
            "shopAddress": report.get("shopAddress"),
            "submittedPrice": report.get("submittedPrice"),
            "priceUnit": report.get("priceUnit"),
            "submissionDate": report.get("submissionDate"),
            "submitterName": report.get("submitterName"),
            "submitterRole": report.get("submitterRole"),
            "location": report.get("location")
        }
        result.append(ReportInDB.from_mongo(report_dict))
    
    return result

@router.get("/history/reviewed", response_model=List[ReportInDB])
async def get_reviewed_reports(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in details field"),
    reason: Optional[str] = Query(None, description="Filter by reason for flag"),
    priceType: Optional[str] = Query(None, description="Filter by price type: RETAIL or WHOLESALE"),
    db: Session = Depends(get_postgres_db)
):
    collection = get_mongo_collection("reports")
    
    # Build query filter for reviewed/dismissed reports
    query = {"status": {"$in": ["REVIEWED", "DISMISSED"]}}
    
    if search:
        query["details"] = {"$regex": search, "$options": "i"}
    
    if reason:
        reason_mapping = {
            "ai_flag_price_high": "AI_FLAG_PRICE_HIGH",
            "user_suggestion": "USER_SUGGESTION"
        }
        mapped_reason = reason_mapping.get(reason.lower(), reason.upper())
        query["reasonForFlag"] = mapped_reason
    
    # Simple MongoDB aggregation to join with price entries only
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "price_entries",
            "localField": "priceEntryId",
            "foreignField": "_id",
            "as": "priceEntry"
        }},
        {"$unwind": {"path": "$priceEntry", "preserveNullAndEmptyArrays": True}}
    ]
    
    # Add price type filter after lookup if specified
    if priceType:
        pipeline.append({"$match": {"priceEntry.type": priceType.upper()}})
    
    # Add sort, skip and limit
    pipeline.extend([
        {"$sort": {"timestamp": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ])
    
    reports_cursor = collection.aggregate(pipeline)
    reports = await reports_cursor.to_list(length=limit)
    
    # Enrich with PostgreSQL data
    enriched_reports = await enrich_reports_with_postgres_data(reports, db)
    
    # Convert to ReportInDB format (normalize timestamps to Asia/Yangon)
    result = []
    for report in enriched_reports:
        ts = report.get("timestamp")
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            report["timestamp"] = ts.astimezone(ZoneInfo("Asia/Yangon"))
        report_dict = {
            "_id": report["_id"],
            "priceEntryId": str(report["priceEntryId"]),
            "reportedByUserId": report["reportedByUserId"],
            "reasonForFlag": report["reasonForFlag"],
            "details": report["details"],
            "status": report["status"],
            "timestamp": report["timestamp"],
            "priceType": report.get("priceType"),
            "itemName": report.get("itemName"),
            "shopName": report.get("shopName"),
            "shopAddress": report.get("shopAddress"),
            "submittedPrice": report.get("submittedPrice"),
            "priceUnit": report.get("priceUnit"),
            "submissionDate": report.get("submissionDate"),
            "submitterName": report.get("submitterName"),
            "submitterRole": report.get("submitterRole"),
            "location": report.get("location")
        }
        result.append(ReportInDB.from_mongo(report_dict))
    
    return result

@router.put("/{report_id}", response_model=ReportInDB)
async def update_report_status(report_id: str, status_update: dict, db: Session = Depends(get_postgres_db)):
    collection = get_mongo_collection("reports")
    
    try:
        object_id = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    # Get the report first to find the user who submitted the price entry
    report = await collection.find_one({"_id": object_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Validate status
    valid_statuses = ["PENDING", "REVIEWED", "DISMISSED"]
    new_status = status_update.get("status")
    action = status_update.get("action")  # "warning", "ban", or "dismiss"
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Get price entry to find the user who submitted it
    price_entries_collection = get_mongo_collection("price_entries")
    price_entry = await price_entries_collection.find_one({"_id": report["priceEntryId"]})
    
    if price_entry and "submittedBy" in price_entry:
        user_id = price_entry["submittedBy"]["id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if user and action == "dismiss":
            # Dismiss the report (no action against user)
            db.commit()
            
            # Create notification for the user that their submission was reviewed
            dismiss_notification = Notification(
                user_id=user.id,
                title="Report Dismissed",
                message="Your price submission has been reviewed and found to be acceptable. No action was taken against your account.",
                category=NotificationCategory.SYSTEM,
                read=False
            )
            db.add(dismiss_notification)
            db.commit()
            
            # Update the report
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": {"status": "DISMISSED", "updatedAt": datetime.now(ZoneInfo("Asia/Yangon")), "action": "dismissed"}}
            )
            
            # Return updated report
            updated_report = await collection.find_one({"_id": object_id})
            return ReportInDB.from_mongo(updated_report)
        
        elif user and action == "warning":
            # Increment warning count
            user.warning_count += 1
            
            # If user reaches 3 warnings, ban them
            if user.warning_count >= 3:
                user.status = UserStatus.BANNED
                db.commit()
                
                # Create notification for the banned user
                ban_notification = Notification(
                    user_id=user.id,
                    title="Account Banned",
                    message=f"Your account has been banned due to receiving 3 warnings. You can no longer access the platform.",
                    category=NotificationCategory.SYSTEM,
                    read=False
                )
                db.add(ban_notification)
                db.commit()
                
                # Update the report
                result = await collection.update_one(
                    {"_id": object_id},
                    {"$set": {"status": "REVIEWED", "updatedAt": datetime.now(ZoneInfo("Asia/Yangon")), "action": "banned"}}
                )
                
                # Return updated report with warning info
                updated_report = await collection.find_one({"_id": object_id})
                response_data = ReportInDB.from_mongo(updated_report)
                response_data.warning_info = {
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "warning_count": user.warning_count,
                    "status": user.status.value,
                    "can_warn": False,
                    "can_ban": False
                }
                return response_data
            else:
                db.commit()
                
                # Create warning notification for the user
                warning_notification = Notification(
                    user_id=user.id,
                    title="Warning Issued",
                    message=f"You have received a warning for your price submission. Current warnings: {user.warning_count}/3. Please ensure your submissions are accurate.",
                    category=NotificationCategory.SYSTEM,
                    read=False
                )
                db.add(warning_notification)
                db.commit()
                
                # Update the report
                result = await collection.update_one(
                    {"_id": object_id},
                    {"$set": {"status": "REVIEWED", "updatedAt": datetime.now(ZoneInfo("Asia/Yangon")), "action": "warned"}}
                )
                
                # Return updated report with warning info
                updated_report = await collection.find_one({"_id": object_id})
                response_data = ReportInDB.from_mongo(updated_report)
                response_data.warning_info = {
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "warning_count": user.warning_count,
                    "status": user.status.value,
                    "can_warn": user.warning_count < 3 and user.status.value != "BANNED",
                    "can_ban": user.warning_count >= 3
                }
                return response_data
        
        elif user and action == "ban":
            # Direct ban
            user.status = UserStatus.BANNED
            db.commit()
            
            # Create notification for the banned user
            ban_notification = Notification(
                user_id=user.id,
                title="Account Banned",
                message=f"Your account has been banned by an administrator. You can no longer access the platform.",
                category=NotificationCategory.SYSTEM,
                read=False
            )
            db.add(ban_notification)
            db.commit()
            
            # Update the report
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": {"status": "REVIEWED", "updatedAt": datetime.now(ZoneInfo("Asia/Yangon")), "action": "banned"}}
            )
            
            # Return updated report with warning info
            updated_report = await collection.find_one({"_id": object_id})
            response_data = ReportInDB.from_mongo(updated_report)
            response_data.warning_info = {
                "user_id": user.id,
                "user_name": user.full_name,
                "warning_count": user.warning_count,
                "status": user.status.value,
                "can_warn": False,
                "can_ban": False
            }
            return response_data
    
    # Update the report without user action (fallback case)
    result = await collection.update_one(
        {"_id": object_id},
        {"$set": {"status": new_status, "updatedAt": datetime.now(ZoneInfo("Asia/Yangon"))}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # If the report was reviewed and there's a user, send a notification
    if new_status == "REVIEWED" and price_entry and "submittedBy" in price_entry:
        user_id = price_entry["submittedBy"]["id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Create notification for the user that their submission was reviewed
            review_notification = Notification(
                user_id=user.id,
                title="Report Reviewed",
                message="Your price submission has been reviewed by an administrator.",
                category=NotificationCategory.SYSTEM,
                read=False
            )
            db.add(review_notification)
            db.commit()
    
    # If the report was dismissed and there's a user, send a notification
    if new_status == "DISMISSED" and price_entry and "submittedBy" in price_entry:
        user_id = price_entry["submittedBy"]["id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Create notification for the user that their submission was dismissed
            dismiss_notification = Notification(
                user_id=user.id,
                title="Report Dismissed",
                message="Your price submission has been reviewed and dismissed. No action was taken against your account.",
                category=NotificationCategory.SYSTEM,
                read=False
            )
            db.add(dismiss_notification)
            db.commit()
    
    # Return updated report
    updated_report = await collection.find_one({"_id": object_id})
    return ReportInDB.from_mongo(updated_report)

@router.get("/{report_id}/user-warning-info")
async def get_user_warning_info(report_id: str, db: Session = Depends(get_postgres_db)):
    """Get warning information for the user who submitted the price entry in this report"""
    collection = get_mongo_collection("reports")
    
    try:
        object_id = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    # Get the report
    report = await collection.find_one({"_id": object_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get price entry to find the user
    price_entries_collection = get_mongo_collection("price_entries")
    price_entry = await price_entries_collection.find_one({"_id": report["priceEntryId"]})
    
    if price_entry and "submittedBy" in price_entry:
        user_id = price_entry["submittedBy"]["id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            return {
                "user_id": user.id,
                "user_name": user.full_name,
                "warning_count": user.warning_count,
                "status": user.status.value,
                "can_warn": user.warning_count < 3 and user.status.value != "BANNED",
                "can_ban": user.warning_count >= 3
            }
    
    return {
        "user_id": None,
        "user_name": "Unknown",
        "warning_count": 0,
        "status": "UNKNOWN",
        "can_warn": False,
        "can_ban": False
    }