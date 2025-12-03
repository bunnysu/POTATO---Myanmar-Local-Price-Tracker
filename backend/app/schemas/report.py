from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Literal, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from bson import ObjectId 

class ReportBase(BaseModel):
    priceEntryId: str  
    reportedByUserId: int
    reasonForFlag: Literal["AI_FLAG_PRICE_HIGH", "USER_SUGGESTION"]
    details: str
    status: Literal["PENDING", "REVIEWED", "DISMISSED"] = "PENDING"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Yangon")))

class ReportInDB(ReportBase):
    id: str = Field(alias="_id")
    # Additional enriched fields from price entry
    priceType: Optional[Literal["WHOLESALE", "RETAIL"]] = None
    itemName: Optional[str] = None
    shopName: Optional[str] = None
    shopAddress: Optional[str] = None
    submittedPrice: Optional[float] = None
    priceUnit: Optional[str] = None
    submissionDate: Optional[datetime] = None
    submitterName: Optional[str] = None
    submitterRole: Optional[str] = None
    location: Optional[str] = None
    warning_info: Optional[dict] = None
    
    @classmethod
    def from_mongo(cls, data: dict):
        if "_id" in data:
            data["_id"] = str(data["_id"])
            # Also set id field for frontend compatibility
            data["id"] = str(data["_id"])
        # Ensure nested references are serialized to strings
        if "priceEntryId" in data and isinstance(data["priceEntryId"], ObjectId):
            data["priceEntryId"] = str(data["priceEntryId"]) 
        return cls(**data)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}  
    )