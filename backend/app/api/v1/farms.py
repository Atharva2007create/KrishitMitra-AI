from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import CropCycle, Farm, FarmerProfile
from app.schemas.domain import FarmCreate, FarmResponse, FarmUpdate
from app.security.dependencies import FarmerUser
from app.services.audit import record_audit

router = APIRouter(prefix="/farms", tags=["farms"])
Session = Annotated[AsyncSession, Depends(get_db)]


async def _profile_id(session: AsyncSession, user_id: UUID) -> UUID:
    value = await session.scalar(select(FarmerProfile.id).where(FarmerProfile.user_id == user_id))
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Create farmer profile first"
        )
    return value


async def _owned_farm(session: AsyncSession, user_id: UUID, farm_id: UUID) -> Farm:
    farm = await session.scalar(
        select(Farm).join(FarmerProfile).where(Farm.id == farm_id, FarmerProfile.user_id == user_id)
    )
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


@router.get("", response_model=list[FarmResponse])
async def list_farms(current_user: FarmerUser, session: Session) -> list[Farm]:
    farms = await session.scalars(
        select(Farm).join(FarmerProfile).where(FarmerProfile.user_id == current_user.id)
    )
    return list(farms)


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(payload: FarmCreate, current_user: FarmerUser, session: Session) -> Farm:
    farm = Farm(
        farmer_profile_id=await _profile_id(session, current_user.id), **payload.model_dump()
    )
    session.add(farm)
    await session.flush()
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="farm.created",
        entity_type="farm",
        entity_id=farm.id,
    )
    await session.commit()
    await session.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(farm_id: UUID, current_user: FarmerUser, session: Session) -> Farm:
    return await _owned_farm(session, current_user.id, farm_id)


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: UUID, payload: FarmUpdate, current_user: FarmerUser, session: Session
) -> Farm:
    farm = await _owned_farm(session, current_user.id, farm_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="farm.updated",
        entity_type="farm",
        entity_id=farm.id,
    )
    await session.commit()
    await session.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(farm_id: UUID, current_user: FarmerUser, session: Session) -> Response:
    farm = await _owned_farm(session, current_user.id, farm_id)
    has_cycles = await session.scalar(select(exists().where(CropCycle.farm_id == farm.id)))
    if has_cycles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Farm with crop cycles cannot be deleted",
        )
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="farm.deleted",
        entity_type="farm",
        entity_id=farm.id,
    )
    await session.execute(delete(Farm).where(Farm.id == farm.id))
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
