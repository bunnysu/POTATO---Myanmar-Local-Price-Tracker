from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_postgres_db
from app.schemas.item import ItemCreate, ItemInDB, ItemUpdate
from app.db import postgres_models as models

router = APIRouter()

@router.post("/", response_model=ItemInDB)
def create_item(item: ItemCreate, db: Session = Depends(get_postgres_db)):
    db_item = db.query(models.Item).filter(models.Item.name == item.name).first()
    if db_item:
        raise HTTPException(status_code=400, detail="Item already exists")
    
    new_item = models.Item(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/", response_model=List[ItemInDB])
def read_items(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    db: Session = Depends(get_postgres_db)
):
    query = db.query(models.Item)
    if category_id is not None:
        query = query.filter(models.Item.category_id == category_id)
    items = query.offset(skip).limit(limit).all()
    return items

@router.get("/{item_id}", response_model=ItemInDB)
def read_item(item_id: int, db: Session = Depends(get_postgres_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemInDB)
def update_item(item_id: int, item_update: ItemUpdate, db: Session = Depends(get_postgres_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if name already exists (if name is being updated)
    if item_update.name and item_update.name != db_item.name:
        existing_item = db.query(models.Item).filter(models.Item.name == item_update.name).first()
        if existing_item:
            raise HTTPException(status_code=400, detail="Item name already exists")
    
    # Validate category exists if category_id is being updated
    if item_update.category_id and item_update.category_id != db_item.category_id:
        category = db.query(models.Category).filter(models.Category.id == item_update.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_postgres_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}
