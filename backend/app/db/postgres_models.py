import enum
from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    Enum as SAEnum,
    ForeignKey,
    DateTime,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy import text
from geoalchemy2 import Geometry  # noqa: F401 (not used currently)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class UserRole(str, enum.Enum):
    USER = "USER"
    CONTRIBUTOR = "CONTRIBUTOR"
    RETAILER = "RETAILER"
    ADMIN = "ADMIN"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    BANNED = "BANNED"
    PENDING = "PENDING"

class ShopStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)  # Add phone number for contributors
    role = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SAEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    warning_count = Column(Integer, default=0)
    
    # Normalized region reference
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    township_id = Column(Integer, ForeignKey("townships.id"), nullable=True)
    image_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, onupdate=text('now()'))

    shops = relationship("Shop", back_populates="owner", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    items = relationship("Item", back_populates="category")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    default_unit = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="items")

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # Yangon, Mandalay
    
class Township(Base):
    __tablename__ = "townships"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)  # Hlaing, Kamayut
    region_id = Column(Integer, ForeignKey("regions.id"))
    latitude = Column(Float)  # Default lat for township
    longitude = Column(Float) # Default long for township
    
    region = relationship("Region")

class Shop(Base):
    __tablename__ = "shops"
    id = Column(Integer, primary_key=True, index=True)
    shop_name = Column(String, index=True, nullable=False)
    address_text = Column(String)
    operating_hours = Column(String)
    phone_number = Column(String)
    status = Column(SAEnum(ShopStatus), default=ShopStatus.UNVERIFIED, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="shops")
    region_id = Column(Integer, ForeignKey("regions.id"))  # Yangon, Mandalay
    township_id = Column(Integer, ForeignKey("townships.id"))  # Hlaing, Kamayut
    region = relationship("Region")
    township = relationship("Township")
    image_url = Column(String, nullable=True)


class NotificationCategory(str, enum.Enum):
    PRICE = "price"
    WATCHLIST = "watchlist"
    SOCIAL = "social"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    category = Column(SAEnum(NotificationCategory), default=NotificationCategory.PRICE, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=text('now()'))


class FavWatch(Base):
    __tablename__ = "fav_watch"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    created_at = Column(DateTime, server_default=text('now()'))