# app/schemas/region.py
from pydantic import BaseModel

class RegionBase(BaseModel):
    name: str

class RegionCreate(RegionBase):
    pass

class RegionInDB(RegionBase):
    id: int
    
    class Config:
        from_attributes = True