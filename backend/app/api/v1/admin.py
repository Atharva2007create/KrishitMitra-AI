from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import GovernmentSource
from app.schemas.domain import AdminHealthResponse, GovernmentSourceResponse
from app.security.dependencies import AdminUser
from app.services.audit import record_audit

router = APIRouter(prefix="/admin", tags=["admin"])
Session = Annotated[AsyncSession, Depends(get_db)]


@router.get("/health", response_model=AdminHealthResponse)
async def admin_health(current_user: AdminUser, session: Session) -> AdminHealthResponse:
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="admin.health_accessed",
        entity_type="system",
    )
    await session.commit()
    return AdminHealthResponse(status="ok", role=current_user.role)


@router.get("/sources", response_model=list[GovernmentSourceResponse])
async def list_sources(current_user: AdminUser, session: Session) -> list[GovernmentSource]:
    record_audit(
        session,
        actor_user_id=current_user.id,
        action="admin.sources_listed",
        entity_type="government_source",
    )
    sources = list(await session.scalars(select(GovernmentSource).order_by(GovernmentSource.name)))
    await session.commit()
    return sources
