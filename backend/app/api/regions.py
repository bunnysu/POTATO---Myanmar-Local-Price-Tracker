from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_postgres_db
from app.db import postgres_models as models
from app.schemas.region import RegionCreate, RegionInDB

router = APIRouter()

@router.post("/", response_model=RegionInDB)
def create_region(region: RegionCreate, db: Session = Depends(get_postgres_db)):
    db_region = models.Region(name=region.name)
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region

@router.get("/", response_model=list[RegionInDB])
def read_regions(db: Session = Depends(get_postgres_db)):
    return db.query(models.Region).all()
