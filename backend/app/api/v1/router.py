from fastapi import APIRouter, HTTPException, status

from app.db.connection import check_database

router = APIRouter()


@router.get("/ready", tags=["system"])
async def readiness() -> dict[str, str]:
    if not await check_database():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return {"status": "ready", "database": "connected"}
