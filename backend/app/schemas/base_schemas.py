from pydantic.json_schema import GetJsonSchemaHandler
from pydantic_core import CoreSchema
from bson import ObjectId
from typing import Any

from pydantic import BaseModel
from typing import Optional

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetJsonSchemaHandler) -> CoreSchema:
        return handler(str)


class NotificationBase(BaseModel):
    title: str
    message: str
    category: str  # price, watchlist, social, system
    read: Optional[bool] = False


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int