from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.core.security import get_current_user
from zoneinfo import ZoneInfo

router = APIRouter()


def _to_myanmar_iso(dt):
    if dt is None:
        return None
    # If timestamp is naive, assume it's UTC, then convert to Asia/Yangon
    if dt.tzinfo is None:
        try:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        except Exception:
            # Fallback: leave as-is
            pass
    try:
        dt_mm = dt.astimezone(ZoneInfo("Asia/Yangon"))
        return dt_mm.isoformat()
    except Exception:
        return dt.isoformat()


@router.get("/", response_model=list[dict])
def list_notifications(
    category: Optional[str] = Query(None),
    unread: Optional[bool] = Query(None),
    db: Session = Depends(get_postgres_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if category:
        q = q.filter(models.Notification.category == models.NotificationCategory(category))
    if unread is not None:
        q = q.filter(models.Notification.read == unread)
    rows = q.order_by(models.Notification.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "category": n.category.value,
            "read": n.read,
            # Send Myanmar-time ISO string so clients can render correctly
            "created_at": _to_myanmar_iso(n.created_at),
        }
        for n in rows
    ]


@router.get("/unread-count", response_model=dict)
def get_unread_count(
    db: Session = Depends(get_postgres_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get the count of unread notifications for the current user"""
    count = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.read == False
    ).count()
    return {"unread_count": count}


@router.post("/", response_model=dict)
def create_notification(
    payload: dict,
    db: Session = Depends(get_postgres_db),
    current_user: models.User = Depends(get_current_user),
):
    # Allow admins to create SYSTEM notifications for any user when user_id is provided
    user_id = payload.get("user_id", current_user.id)
    if payload.get("category") == "system" and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can create system notifications")
    try:
        n = models.Notification(
            user_id=user_id,
            title=payload["title"],
            message=payload["message"],
            category=models.NotificationCategory(payload.get("category", "price")),
            read=payload.get("read", False),
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        return {"id": n.id}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.post("/{notification_id}/read", response_model=dict)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_postgres_db),
    current_user: models.User = Depends(get_current_user),
):
    n = db.query(models.Notification).filter(models.Notification.id == notification_id, models.Notification.user_id == current_user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.add(n)
    db.commit()
    return {"status": "ok"}


@router.delete("/{notification_id}", response_model=dict)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_postgres_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a notification - only the owner can delete their own notifications"""
    n = db.query(models.Notification).filter(models.Notification.id == notification_id, models.Notification.user_id == current_user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(n)
    db.commit()
    return {"message": "Notification deleted successfully"}


@router.post("/broadcast", response_model=dict)
def broadcast_system_announcement(
    payload: dict,
    db: Session = Depends(get_postgres_db),
    # TODO: Re-enable authentication when frontend auth is implemented
    # current_user: models.User = Depends(get_current_user),
):
    """
    Broadcast a system announcement to all active users.
    Temporarily disabled authentication for testing.
    """
    # TODO: Re-enable admin check when authentication is implemented
    # Check if user is admin
    # if current_user.role != models.UserRole.ADMIN:
    #     raise HTTPException(status_code=403, detail="Only administrators can broadcast announcements")
    
    # Validate payload
    if not payload.get("title") or not payload.get("message"):
        raise HTTPException(status_code=400, detail="Both title and message are required")
    
    try:
        # Get all active users
        active_users = db.query(models.User).filter(models.User.status == models.UserStatus.ACTIVE).all()
        
        if not active_users:
            raise HTTPException(status_code=404, detail="No active users found")
        
        notifications_created = 0
        
        # Create notification for each active user
        for user in active_users:
            notification = models.Notification(
                user_id=user.id,
                title=payload["title"],
                message=payload["message"],
                category=models.NotificationCategory.SYSTEM,
                read=False,
            )
            db.add(notification)
            notifications_created += 1
        
        # Commit all notifications
        db.commit()
        
        return {
            "success": True,
            "message": f"Announcement sent to {notifications_created} users",
            "notifications_created": notifications_created
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to broadcast announcement: {str(e)}")

