# FastAPI app setup and main router
#This file starts your application. It creates the FastAPI app and includes all the API routers from the app/api directory.
# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, users, shops, items, prices, reports, reviews
from app.db.postgres_models import Base
from app.db.database import engine, get_postgres_db
from sqlalchemy.orm import Session

# Database tables တွေကို create လုပ်ဖို့
Base.metadata.create_all(bind=engine)

def seed_database():
    """Seed the database with initial data"""
    from app.db import postgres_models as models
    
    # Create a session
    db = next(get_postgres_db())
    
    try:
        # Check if regions already exist
        existing_regions = db.query(models.Region).count()
        if existing_regions == 0:
            # Create sample regions
            regions = [
                models.Region(name="Yangon"),
                models.Region(name="Mandalay"),
                models.Region(name="Nay Pyi Taw"),
                models.Region(name="Bago"),
                models.Region(name="Mawlamyine"),
            ]
            
            for region in regions:
                db.add(region)
            
            db.commit()
            print("✅ Regions seeded successfully")
            
            # Get the created regions to create townships
            yangon = db.query(models.Region).filter(models.Region.name == "Yangon").first()
            mandalay = db.query(models.Region).filter(models.Region.name == "Mandalay").first()
            naypyitaw = db.query(models.Region).filter(models.Region.name == "Nay Pyi Taw").first()
            
            # Create sample townships
            townships = [
                models.Township(name="Hlaing", region_id=yangon.id, latitude=16.8661, longitude=96.1951),
                models.Township(name="Kamayut", region_id=yangon.id, latitude=16.8000, longitude=96.1500),
                models.Township(name="Sanchaung", region_id=yangon.id, latitude=16.7833, longitude=96.1333),
                models.Township(name="Chan Aye Tharzan", region_id=mandalay.id, latitude=21.9588, longitude=96.0891),
                models.Township(name="Amarapura", region_id=mandalay.id, latitude=21.9000, longitude=96.0500),
                models.Township(name="Pyinmana", region_id=naypyitaw.id, latitude=19.7500, longitude=96.2167),
                models.Township(name="Lewe", region_id=naypyitaw.id, latitude=19.6833, longitude=96.2167),
            ]
            
            for township in townships:
                db.add(township)
            
            db.commit()
            print("✅ Townships seeded successfully")
            
            # Create sample categories
            categories = [
                models.Category(name="Oils & Spices"),
                models.Category(name="Grains & Cereals"),
                models.Category(name="Vegetables & Fruits"),
                models.Category(name="Meat & Fish"),
                models.Category(name="Dairy & Eggs"),
                models.Category(name="Beverages"),
            ]
            
            for category in categories:
                db.add(category)
            
            db.commit()
            print("✅ Categories seeded successfully")
            
            # Get the created categories to create items
            oils_category = db.query(models.Category).filter(models.Category.name == "Oils & Spices").first()
            grains_category = db.query(models.Category).filter(models.Category.name == "Grains & Cereals").first()
            vegetables_category = db.query(models.Category).filter(models.Category.name == "Vegetables & Fruits").first()
            
            # Create sample items
            items = [
                models.Item(name="Peanut Oil", default_unit="liter", category_id=oils_category.id),
                models.Item(name="Cooking Oil", default_unit="liter", category_id=oils_category.id),
                models.Item(name="Rice", default_unit="kg", category_id=grains_category.id),
                models.Item(name="Beans", default_unit="kg", category_id=grains_category.id),
                models.Item(name="Tomatoes", default_unit="kg", category_id=vegetables_category.id),
                models.Item(name="Onions", default_unit="kg", category_id=vegetables_category.id),
                models.Item(name="Potatoes", default_unit="kg", category_id=vegetables_category.id),
            ]
            
            for item in items:
                db.add(item)
            
            db.commit()
            print("✅ Items seeded successfully")
            
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

# Seed the database
seed_database()

app = FastAPI(title=settings.PROJECT_NAME)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(auth.router, tags=["Authentication"])
# app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME}"}