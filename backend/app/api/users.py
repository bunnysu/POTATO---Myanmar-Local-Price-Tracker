from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.schemas.user import (
    UserCreate,
    UserInDB,
    UserUpdate,
    UserResponse,
    RetailerRegistrationRequest,
    RetailerRegistrationResponse,
)
from app.schemas.shop import ShopCreate, ShopResponse
from app.core import security
from app.core.security import get_current_user, get_current_admin_user, get_password_hash, verify_password

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_postgres_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = security.get_password_hash(user.password)
    
    # Create user
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        phone_number=user.phone_number,
        region_id=user.region_id,
        township_id=user.township_id,
        image_url=user.image_url,
        role=user.role
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )

@router.post("/register/retailer", response_model=RetailerRegistrationResponse)
def register_retailer(
    registration_data: RetailerRegistrationRequest,
    db: Session = Depends(get_postgres_db)
):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == registration_data.user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Email already registered"
        )
    
    # Validate user role
    if registration_data.user.role != models.UserRole.RETAILER:
        raise HTTPException(
            status_code=400,
            detail="User role must be RETAILER for retailer registration"
        )
    
    try:
        # Hash password
        hashed_password = security.get_password_hash(registration_data.user.password)
        
        # Create user
        db_user = models.User(
            email=registration_data.user.email,
            full_name=registration_data.user.full_name,
            hashed_password=hashed_password,
            phone_number=registration_data.user.phone_number,
            region_id=registration_data.user.region_id,
            township_id=registration_data.user.township_id,
            image_url=registration_data.user.image_url,
            role=registration_data.user.role
        )
        
        db.add(db_user)
        db.flush()  # Get the user ID without committing
        
        # Create shop
        db_shop = models.Shop(
            shop_name=registration_data.shop_name,
            address_text=registration_data.address_text,
            operating_hours=registration_data.operating_hours,
            phone_number=registration_data.shop_phone_number,
            status=models.ShopStatus.UNVERIFIED,
            owner_user_id=db_user.id,
            region_id=registration_data.shop_region_id,
            township_id=registration_data.shop_township_id
        )
        
        db.add(db_shop)
        db.commit()
        db.refresh(db_user)
        db.refresh(db_shop)
        
        # Build structured response using schemas so Pydantic can serialize properly
        return {
            "user": db_user,
            "shop": db_shop,
            "message": "Retailer registered successfully",
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to register retailer"
        )

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_postgres_db)):
    return register_user(user, db)

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_postgres_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0, description="Skip N users"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of users"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_postgres_db)
    # TODO: Add admin authentication back when frontend auth is implemented
    # current_user: models.User = Depends(get_current_admin_user)
):
    """
    List all users with optional filtering and pagination.
    TODO: Add admin authentication when frontend auth is implemented.
    """
    query = db.query(models.User)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.User.full_name.ilike(search_term)) |
            (models.User.email.ilike(search_term))
        )
    
    # Apply role filter
    if role:
        try:
            # Convert to uppercase to match enum values
            role_upper = role.upper()
            user_role = models.UserRole(role_upper)
            query = query.filter(models.User.role == user_role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {role}. Valid roles are: USER, CONTRIBUTOR, RETAILER, ADMIN"
            )
    
    # Apply status filter
    if status:
        try:
            # Convert to uppercase to match enum values
            status_upper = status.upper()
            user_status = models.UserStatus(status_upper)
            query = query.filter(models.User.status == user_status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid statuses are: ACTIVE, PENDING, BANNED"
            )
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    # Filter out admin users from the results
    non_admin_users = [user for user in users if user.role != models.UserRole.ADMIN]
    
    return non_admin_users

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Update current authenticated user
@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_postgres_db),
    current_user: models.User = Depends(get_current_user),
):
    # Update allowed fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone_number is not None:
        current_user.phone_number = user_update.phone_number
    if user_update.region_id is not None:
        current_user.region_id = user_update.region_id
    if user_update.township_id is not None:
        current_user.township_id = user_update.township_id
    if user_update.role is not None:
        current_user.role = user_update.role
    if user_update.status is not None:
        current_user.status = user_update.status
    if user_update.image_url is not None:
        current_user.image_url = user_update.image_url

    try:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update user",
        )


@router.post("/change-password", response_model=dict)
def change_password(
    password_data: dict,
    db: Session = Depends(get_postgres_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Change user password for the authenticated user.
    """
    try:
        # current_user is now the authenticated user from JWT token
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate required fields
        if not password_data.get("current_password") or not password_data.get("new_password"):
            raise HTTPException(status_code=400, detail="Current password and new password are required")
        
        # Verify current password for the authenticated user
        if not verify_password(password_data["current_password"], current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Validate new password strength
        new_password = password_data["new_password"]
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")
        
        # Hash the new password
        new_hashed_password = get_password_hash(new_password)
        
        # Update user's password
        current_user.hashed_password = new_hashed_password
        db.commit()
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error changing password: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_postgres_db)):
    """
    Delete a user by ID.
    TODO: Add admin authentication when frontend auth is implemented.
    """
    try:
        # Find the user
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f"Attempting to delete user: {user.full_name} (ID: {user.id}, Role: {user.role})")
        
        # Prevent deletion of admin users (optional security measure)
        if user.role == models.UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot delete admin users")
        
        # Check for foreign key constraints and delete related data first
        print(f"Checking for related data before deletion...")
        
        # Delete related notifications
        notifications_count = db.query(models.Notification).filter(models.Notification.user_id == user_id).count()
        if notifications_count > 0:
            print(f"Deleting {notifications_count} notifications for user {user_id}")
            db.query(models.Notification).filter(models.Notification.user_id == user_id).delete()
        
        # Delete related favorite/watch entries
        fav_watch_count = db.query(models.FavWatch).filter(models.FavWatch.user_id == user_id).count()
        if fav_watch_count > 0:
            print(f"Deleting {fav_watch_count} favorite/watch entries for user {user_id}")
            db.query(models.FavWatch).filter(models.FavWatch.user_id == user_id).delete()
        
        # Delete related shops (if user is a retailer)
        # Note: Shop has cascade="all, delete-orphan" in the model, but let's be explicit
        shop_count = db.query(models.Shop).filter(models.Shop.owner_user_id == user_id).count()
        if shop_count > 0:
            print(f"Deleting {shop_count} shops for user {user_id}")
            db.query(models.Shop).filter(models.Shop.owner_user_id == user_id).delete()
        
        print(f"All related data deleted. Now deleting user...")
        
        # Delete the user
        db.delete(user)
        db.commit()
        print(f"Successfully deleted user: {user.full_name}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting user {user_id}: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        
        # Check for specific database constraint errors
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete user due to existing related data. Please remove related records first."
            )
        elif "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete user due to unique constraint violation."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to delete user: {str(e)}"
            )