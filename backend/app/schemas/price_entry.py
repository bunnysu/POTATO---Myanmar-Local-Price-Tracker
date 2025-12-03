from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Literal, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from bson import ObjectId
from .base_schemas import PyObjectId

class SubmittedBy(BaseModel):
    id: int
    role: Literal["CONTRIBUTOR", "RETAILER", "USER", "ADMIN"]

class LocationInfo(BaseModel):
    region_id: Optional[int] = None
    township_id: int

class PriceEntryBase(BaseModel):
    itemId: int
    type: Literal["WHOLESALE", "RETAIL"]
    price: float
    unit: str
    # Optional to allow deriving from shop
    location: Optional[LocationInfo] = None
    submittedBy: Optional[SubmittedBy] = None
    shopId: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Yangon")))

class PriceEntryInDB(PriceEntryBase):
    id: str = Field(alias="_id")
    region_name: Optional[str] = None
    township_name: Optional[str] = None
    coordinates: Optional[dict] = None
    shop_name: Optional[str] = None
    
    @classmethod
    def from_mongo(cls, data: dict):
        if "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )