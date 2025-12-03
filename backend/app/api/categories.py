from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_postgres_db
from app.schemas.category import CategoryCreate, CategoryInDB, CategoryUpdate
from app.db import postgres_models as models

router = APIRouter()

@router.post("/", response_model=CategoryInDB)
def create_category(category: CategoryCreate, db: Session = Depends(get_postgres_db)):
    db_category = db.query(models.Category).filter(models.Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    new_category = models.Category(**category.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/", response_model=List[CategoryInDB])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_postgres_db)):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories

@router.get("/{category_id}", response_model=CategoryInDB)
def read_category(category_id: int, db: Session = Depends(get_postgres_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryInDB)
def update_category(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_postgres_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if name already exists (if name is being updated)
    if category_update.name and category_update.name != db_category.name:
        existing_category = db.query(models.Category).filter(models.Category.name == category_update.name).first()
        if existing_category:
            raise HTTPException(status_code=400, detail="Category name already exists")
    
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_postgres_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has items
    items_count = db.query(models.Item).filter(models.Item.category_id == category_id).count()
    if items_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category that contains items")
    
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}
