from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .categories import router as categories_router
from .items import router as items_router
from .shops import router as shops_router
from .prices import router as prices_router
from .reviews import router as reviews_router
from .reports import router as reports_router
from .regions import router as regions_router  # Make sure this line exists
from .townships import router as townships_router  # If you have townships
from .fav_watch import router as fav_watch_router
# from .price_ratings import router as price_ratings_router  # Deprecated - using reviews instead
from .notifications import router as notifications_router
from .uploads import router as uploads_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(categories_router, prefix="/categories", tags=["categories"])
router.include_router(items_router, prefix="/items", tags=["items"])
router.include_router(shops_router, prefix="/shops", tags=["shops"])
router.include_router(prices_router, prefix="/prices", tags=["prices"])
router.include_router(reviews_router, prefix="/reviews", tags=["reviews"])
router.include_router(reports_router, prefix="/reports", tags=["reports"])
router.include_router(regions_router, prefix="/regions", tags=["regions"])  # Make sure this line exists
router.include_router(townships_router, prefix="/townships", tags=["townships"])  # Uncomment if you have townships
router.include_router(fav_watch_router, prefix="/fav-watch", tags=["favorites"])
# router.include_router(price_ratings_router, prefix="/price-ratings", tags=["price-ratings"])  # Deprecated - using reviews instead
router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
router.include_router(uploads_router, prefix="/uploads", tags=["uploads"]) 
