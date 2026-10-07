from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import CropCycle, Farm, FarmerProfile
from app.models.enums import CropCycleStatus
from app.schemas.domain import CropCycleCreate, CropCycleResponse, CropCycleUpdate
from app.security.dependencies import FarmerUser
from app.services.audit import record_audit

router = APIRouter(prefix="/crop-cycles", tags=["crop cycles"])
Session = Annotated[AsyncSession, Depends(get_db)]
TRANSITIONS = {
    CropCycleStatus.PLANNED: {CropCycleStatus.ACTIVE, CropCycleStatus.CANCELLED},
    CropCycleStatus.ACTIVE: {CropCycleStatus.HARVESTED, CropCycleStatus.CANCELLED},
    CropCycleStatus.HARVESTED: set(),
    CropCycleStatus.CANCELLED: set(),
}


def _owned_query(user_id: UUID) -> Select[CropCycle]:
    return select(CropCycle).join(Farm).join(FarmerProfile).where(FarmerProfile.user_id == user_id)


async def _owned_cycle(session: AsyncSession, user_id: UUID, cycle_id: UUID) -> CropCycle:
    cycle = await session.scalar(_owned_query(user_id).where(CropCycle.id == cycle_id))
    if cycle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop cycle not found")
    return cycle


async def _assert_owned_farm(session: AsyncSession, user_id: UUID, farm_id: UUID) -> None:
    owned = await session.scalar(
        select(Farm.id)
        .join(FarmerProfile)
        .where(Farm.id == farm_id, FarmerProfile.user_id == user_id)
    )
    if owned is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")


@router.get("", response_model=list[CropCycleResponse])
async def list_crop_cycles(current_user: FarmerUser, session: Session) -> list[CropCycle]:
    return list(await session.scalars(_owned_query(current_user.id)))


@router.post("", response_model=CropCycleResponse, status_code=status.HTTP_201_CREATED)
async def create_crop_cycle(
    payload: CropCycleCreate, current_user: FarmerUser, session: Session
) -> CropCycle:
    await _assert_owned_farm(session, current_user.id, payload.farm_id)
    cycle = CropCycle(**payload.model_dump())
    session.add(cycle)
    await session.flush()
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="crop_cycle.created",
        entity_type="crop_cycle",
        entity_id=cycle.id,
    )
    await session.commit()
    await session.refresh(cycle)
    return cycle


@router.get("/{crop_cycle_id}", response_model=CropCycleResponse)
async def get_crop_cycle(
    crop_cycle_id: UUID, current_user: FarmerUser, session: Session
) -> CropCycle:
    return await _owned_cycle(session, current_user.id, crop_cycle_id)


@router.patch("/{crop_cycle_id}", response_model=CropCycleResponse)
async def update_crop_cycle(
    crop_cycle_id: UUID,
    payload: CropCycleUpdate,
    current_user: FarmerUser,
    session: Session,
) -> CropCycle:
    cycle = await _owned_cycle(session, current_user.id, crop_cycle_id)
    values = payload.model_dump(exclude_unset=True)
    next_status = values.get("status")
    if next_status is not None and next_status != cycle.status:
        if next_status not in TRANSITIONS[cycle.status]:
            raise HTTPException(status_code=400, detail="Invalid crop-cycle status transition")
        if next_status == CropCycleStatus.HARVESTED and values.get("actual_harvest_date") is None:
            raise HTTPException(status_code=400, detail="HARVESTED requires actual_harvest_date")
    for field, value in values.items():
        setattr(cycle, field, value)
    harvest_dates = [cycle.expected_harvest_date, cycle.actual_harvest_date]
    if any(value is not None and value < cycle.sowing_date for value in harvest_dates):
        raise HTTPException(status_code=400, detail="Harvest date cannot precede sowing date")
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="crop_cycle.updated",
        entity_type="crop_cycle",
        entity_id=cycle.id,
    )
    await session.commit()
    await session.refresh(cycle)
    return cycle


@router.delete("/{crop_cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crop_cycle(
    crop_cycle_id: UUID, current_user: FarmerUser, session: Session
) -> Response:
    cycle = await _owned_cycle(session, current_user.id, crop_cycle_id)
    if cycle.status in {CropCycleStatus.ACTIVE, CropCycleStatus.HARVESTED}:
        raise HTTPException(status_code=409, detail="Active or harvested cycles cannot be deleted")
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="crop_cycle.deleted",
        entity_type="crop_cycle",
        entity_id=cycle.id,
    )
    await session.execute(delete(CropCycle).where(CropCycle.id == cycle.id))
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
