from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Optional
from datetime import datetime


class FavWatchBase(BaseModel):
    shop_id: Optional[int] = None
    item_id: Optional[int] = None


class FavWatchInDB(FavWatchBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


