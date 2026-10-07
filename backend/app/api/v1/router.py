from fastapi import APIRouter, HTTPException, status

from app.api.v1 import admin, chat, crop_cycles, farms, feedback, me, profiles
from app.db.connection import check_database

router = APIRouter()
router.include_router(me.router)
router.include_router(profiles.router)
router.include_router(farms.router)
router.include_router(crop_cycles.router)
router.include_router(chat.router)
router.include_router(feedback.router)
router.include_router(admin.router)


@router.get("/ready", tags=["system"])
async def readiness() -> dict[str, str]:
    if not await check_database():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return {"status": "ready", "database": "connected"}
