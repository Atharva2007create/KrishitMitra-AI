from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import FarmerProfile
from app.schemas.domain import FarmerProfileCreate, FarmerProfileResponse, FarmerProfileUpdate
from app.security.dependencies import FarmerUser
from app.services.audit import record_audit

router = APIRouter(prefix="/farmer/profile", tags=["farmer profile"])
Session = Annotated[AsyncSession, Depends(get_db)]


async def _profile(session: AsyncSession, user_id: object) -> FarmerProfile | None:
    return await session.scalar(select(FarmerProfile).where(FarmerProfile.user_id == user_id))


@router.get("", response_model=FarmerProfileResponse)
async def get_profile(current_user: FarmerUser, session: Session) -> FarmerProfile:
    profile = await _profile(session, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Farmer profile not found"
        )
    return profile


@router.post("", response_model=FarmerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: FarmerProfileCreate, current_user: FarmerUser, session: Session
) -> FarmerProfile:
    if await _profile(session, current_user.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Farmer profile exists")
    profile = FarmerProfile(user_id=current_user.id, **payload.model_dump())
    session.add(profile)
    await session.flush()
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="farmer_profile.created",
        entity_type="farmer_profile",
        entity_id=profile.id,
    )
    await session.commit()
    await session.refresh(profile)
    return profile


@router.patch("", response_model=FarmerProfileResponse)
async def update_profile(
    payload: FarmerProfileUpdate, current_user: FarmerUser, session: Session
) -> FarmerProfile:
    profile = await _profile(session, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Farmer profile not found"
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="farmer_profile.updated",
        entity_type="farmer_profile",
        entity_id=profile.id,
    )
    await session.commit()
    await session.refresh(profile)
    return profile
