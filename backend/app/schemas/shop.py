from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.db.postgres_models import ShopStatus

class Location(BaseModel):
    latitude: float
    longitude: float

class ShopBase(BaseModel):
    shop_name: str
    address_text: Optional[str] = None
    operating_hours: Optional[str] = None
    phone_number: Optional[str] = None
    region_id: Optional[int] = None
    township_id: Optional[int] = None
    image_url: Optional[str] = None

class ShopCreate(ShopBase):
    owner_user_id: int

class ShopUpdate(BaseModel):
    shop_name: Optional[str] = None
    address_text: Optional[str] = None
    operating_hours: Optional[str] = None
    phone_number: Optional[str] = None
    region_id: Optional[int] = None
    township_id: Optional[int] = None
    status: Optional[ShopStatus] = None
    image_url: Optional[str] = None

class TownshipInfo(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    model_config = ConfigDict(from_attributes=True)

class ShopInDB(ShopBase):
    id: int
    status: ShopStatus
    owner_user_id: int
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class ShopResponse(ShopBase):
    id: int
    status: ShopStatus
    owner_user_id: int
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)