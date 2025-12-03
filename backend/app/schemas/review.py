from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime
from zoneinfo import ZoneInfo
from bson import ObjectId
from typing import Optional, Dict, Any

class ReviewBase(BaseModel):
    shopId: int
    userId: int
    rating: int = Field(ge=1, le=5)
    comment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Yangon")))
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    sentiment_details: Optional[Dict[str, Any]] = None

class ReviewInDB(ReviewBase):
    id: str = Field(alias="_id")
    
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