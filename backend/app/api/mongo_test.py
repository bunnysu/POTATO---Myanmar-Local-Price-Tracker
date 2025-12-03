from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/mongo-uri")
def show_mongo_uri():
    return {"mongo_uri": settings.MONGO_DATABASE_URI}