from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.connection import get_db
from app.models.entities import User
from app.schemas.domain import MeResponse
from app.security.dependencies import CurrentUser

router = APIRouter(tags=["identity"])


@router.get("/me", response_model=MeResponse, summary="Get the authenticated application user")
async def get_me(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    user = await session.scalar(
        select(User).options(selectinload(User.farmer_profile)).where(User.id == current_user.id)
    )
    return MeResponse.model_validate(user)
