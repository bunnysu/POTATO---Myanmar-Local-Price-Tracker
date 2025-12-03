from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from app.db.postgres_models import UserRole, UserStatus
from app.schemas.shop import ShopResponse

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER
    phone_number: Optional[str] = None
    region_id: Optional[int] = None
    township_id: Optional[int] = None
    image_url: Optional[str] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        # Allow USER and CONTRIBUTOR to self-register; block ADMIN via this endpoint
        if v in [UserRole.ADMIN]:
            raise ValueError("Admins cannot register through this endpoint")
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None
    phone_number: Optional[str] = None
    region_id: Optional[int] = None
    township_id: Optional[int] = None
    image_url: Optional[str] = None

class UserInDB(UserBase):
    id: int
    role: UserRole
    status: UserStatus
    warning_count: int
    phone_number: Optional[str] = None
    region_id: Optional[int] = None
    township_id: Optional[int] = None
    image_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    status: UserStatus
    warning_count: int
    phone_number: Optional[str] = None
    region_id: Optional[int] = None
    township_id: Optional[int] = None
    image_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RetailerRegistrationRequest(BaseModel):
    user: UserCreate
    shop_name: str
    address_text: Optional[str] = None
    operating_hours: Optional[str] = None
    shop_phone_number: Optional[str] = None
    shop_region_id: Optional[int] = None
    shop_township_id: Optional[int] = None

class RetailerRegistrationResponse(BaseModel):
    user: UserResponse
    shop: ShopResponse
    message: str
    model_config = ConfigDict(from_attributes=True)