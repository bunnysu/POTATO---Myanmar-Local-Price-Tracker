
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import shutil
from pathlib import Path

from app.db.database import get_postgres_db
from app.core.security import get_current_user
from app.schemas.user import UserInDB
from app.db import postgres_models as models

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/user-profile-image")
async def upload_user_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Upload a profile image for the current user.
    """
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_path = UPLOAD_DIR / f"user_{current_user.id}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store just the filename in database for easier URL construction
    user.image_url = file_path.name
    db.commit()

    # Return the full URL for frontend
    full_url = f"http://localhost:8000/api/uploads/{file_path.name}"
    return {"file_path": str(file_path), "url": full_url}

@router.post("/shop-banner-image/{shop_id}")
async def upload_shop_banner_image(
    shop_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_postgres_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Upload a banner image for a shop.
    """
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Check if the current user is the owner of the shop
    if shop.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this shop")

    file_path = UPLOAD_DIR / f"shop_{shop_id}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    shop.image_url = str(file_path)
    db.commit()

    return {"file_path": str(file_path)}

@router.get("/{file_path:path}")
async def read_file(file_path: str):
    return FileResponse(UPLOAD_DIR / file_path)
