from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class ItemInDB(BaseModel):
    id: int
    name: str
    default_unit: str
    model_config = ConfigDict(from_attributes=True)

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None

class CategoryInDB(CategoryBase):
    id: int
    items: List[ItemInDB] = []
    model_config = ConfigDict(from_attributes=True)
