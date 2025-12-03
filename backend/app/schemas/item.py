from pydantic import BaseModel, ConfigDict
from typing import Optional

class CategoryInfo(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class ItemBase(BaseModel):
    name: str
    default_unit: str
    category_id: int

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    default_unit: Optional[str] = None
    category_id: Optional[int] = None

class ItemInDB(ItemBase):
    id: int
    category: CategoryInfo
    model_config = ConfigDict(from_attributes=True)
