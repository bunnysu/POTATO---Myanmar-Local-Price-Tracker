from pydantic import BaseModel, ConfigDict
from typing import Optional

class TownshipBase(BaseModel):
    name: str
    region_id: int
    latitude: float
    longitude: float

class TownshipCreate(TownshipBase):
    pass

class TownshipInDB(TownshipBase):
    id: int
    model_config = ConfigDict(from_attributes=True)