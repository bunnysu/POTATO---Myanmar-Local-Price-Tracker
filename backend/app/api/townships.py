from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.schemas.township import TownshipCreate, TownshipInDB

router = APIRouter()

@router.post("/", response_model=TownshipInDB)
def create_township(township: TownshipCreate, db: Session = Depends(get_postgres_db)):
    # Check if region exists
    db_region = db.query(models.Region).filter(models.Region.id == township.region_id).first()
    if not db_region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    db_township = models.Township(
        name=township.name,
        region_id=township.region_id,
        latitude=township.latitude,
        longitude=township.longitude
    )
    db.add(db_township)
    db.commit()
    db.refresh(db_township)
    return db_township

@router.get("/", response_model=list[TownshipInDB])
def read_townships(region_id: int = None, db: Session = Depends(get_postgres_db)):
    query = db.query(models.Township)
    if region_id:
        query = query.filter(models.Township.region_id == region_id)
    return query.all()