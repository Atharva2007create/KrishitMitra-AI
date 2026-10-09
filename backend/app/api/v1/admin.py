from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.connection import get_db
from app.models.entities import (
    AuditLog,
    ChatSession,
    CropCycle,
    Farm,
    FarmerProfile,
    Feedback,
    GovernmentSource,
    ImageAnalysis,
    IngestionJob,
    SourceDocument,
    User,
)
from app.schemas.domain import AdminHealthResponse
from app.security.dependencies import AdminUser
from app.services.audit import record_audit

router = APIRouter(prefix="/admin", tags=["admin"])
Session = Annotated[AsyncSession, Depends(get_db)]


def _value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID | date | datetime | Decimal):
        return str(value)
    return value


def _safe_metadata(value: Any) -> Any:
    """Redact credential-like values before operational metadata reaches a browser."""
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]"
            if any(
                marker in str(key).lower()
                for marker in ("secret", "token", "password", "credential", "api_key")
            )
            else _safe_metadata(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_safe_metadata(item) for item in value]
    return _value(value)


async def _count(session: AsyncSession, model: type[Any]) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)) or 0)


async def _audit(session: AsyncSession, user: User, action: str, entity: str) -> None:
    record_audit(session, actor_user_id=user.id, action=action, entity_type=entity)
    await session.commit()


@router.get("/health", response_model=AdminHealthResponse)
async def admin_health(current_user: AdminUser, session: Session) -> AdminHealthResponse:
    await _audit(session, current_user, "admin.health_accessed", "system")
    return AdminHealthResponse(status="ok", role=current_user.role)


@router.get("/dashboard")
async def dashboard(current_user: AdminUser, session: Session) -> dict[str, Any]:
    counts = {
        "users": await _count(session, User),
        "farms": await _count(session, Farm),
        "crop_cycles": await _count(session, CropCycle),
        "chat_sessions": await _count(session, ChatSession),
        "sources": await _count(session, GovernmentSource),
        "documents": await _count(session, SourceDocument),
        "ingestion_jobs": await _count(session, IngestionJob),
        "feedback": await _count(session, Feedback),
        "image_analyses": await _count(session, ImageAnalysis),
    }
    ingestion = {
        str(_value(key)): int(value)
        for key, value in (
            await session.execute(
                select(IngestionJob.status, func.count()).group_by(IngestionJob.status)
            )
        ).all()
    }
    images = {
        str(_value(key)): int(value)
        for key, value in (
            await session.execute(
                select(ImageAnalysis.status, func.count()).group_by(ImageAnalysis.status)
            )
        ).all()
    }
    await _audit(session, current_user, "admin.dashboard_viewed", "system")
    return {"counts": counts, "ingestion_by_status": ingestion, "images_by_status": images}


@router.get("/users")
async def list_users(current_user: AdminUser, session: Session) -> list[dict[str, Any]]:
    users = list(
        await session.scalars(
            select(User)
            .options(selectinload(User.farmer_profile))
            .order_by(User.created_at.desc())
            .limit(200)
        )
    )
    result = [
        {
            "id": str(user.id),
            "role": _value(user.role),
            "email": user.email,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "name": user.farmer_profile.full_name if user.farmer_profile else None,
            "last_login_at": _value(user.last_login_at),
            "created_at": _value(user.created_at),
        }
        for user in users
    ]
    await _audit(session, current_user, "admin.users_listed", "user")
    return result


@router.get("/users/{user_id}")
async def user_detail(user_id: UUID, current_user: AdminUser, session: Session) -> dict[str, Any]:
    user = await session.scalar(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.farmer_profile)
            .selectinload(FarmerProfile.farms)
            .selectinload(Farm.crop_cycles)
        )
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    profile = user.farmer_profile
    result: dict[str, Any] = {
        "id": str(user.id),
        "role": _value(user.role),
        "email": user.email,
        "phone_number": user.phone_number,
        "is_active": user.is_active,
        "last_login_at": _value(user.last_login_at),
        "created_at": _value(user.created_at),
        "profile": None,
    }
    if profile:
        result["profile"] = {
            "id": str(profile.id),
            "full_name": profile.full_name,
            "preferred_language": _value(profile.preferred_language),
            "location": {
                "state": profile.state,
                "district": profile.district,
                "taluka": profile.taluka,
                "village": profile.village,
            },
            "farms": [
                {
                    "id": str(farm.id),
                    "name": farm.name,
                    "area_value": _value(farm.area_value),
                    "area_unit": _value(farm.area_unit),
                    "soil_type": farm.soil_type,
                    "irrigation_type": farm.irrigation_type,
                    "crop_cycles": [
                        {
                            "id": str(cycle.id),
                            "crop_name": cycle.crop_name,
                            "crop_variety": cycle.crop_variety,
                            "status": _value(cycle.status),
                            "sowing_date": _value(cycle.sowing_date),
                            "estimated_crop_stage": cycle.estimated_crop_stage,
                        }
                        for cycle in farm.crop_cycles
                    ],
                }
                for farm in profile.farms
            ],
        }
    await _audit(session, current_user, "admin.user_viewed", "user")
    return result


@router.get("/sources")
async def list_sources(current_user: AdminUser, session: Session) -> list[dict[str, Any]]:
    sources = list(await session.scalars(select(GovernmentSource).order_by(GovernmentSource.name)))
    result = [
        {
            "id": str(source.id),
            "name": source.name,
            "organization": source.organization,
            "base_url": source.base_url,
            "source_type": source.source_type,
            "is_active": source.is_active,
            "trust_status": _value(source.trust_status),
            "last_verified_at": _value(source.last_verified_at),
            "notes": source.notes,
        }
        for source in sources
    ]
    await _audit(session, current_user, "admin.sources_listed", "government_source")
    return result


@router.get("/documents")
async def list_documents(current_user: AdminUser, session: Session) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(SourceDocument, GovernmentSource)
            .join(GovernmentSource, SourceDocument.government_source_id == GovernmentSource.id)
            .order_by(SourceDocument.created_at.desc())
            .limit(200)
        )
    ).all()
    result = [
        {
            "id": str(item.id),
            "title": item.title,
            "source_name": source.name,
            "source_url": item.source_url,
            "document_type": item.document_type,
            "crop": item.crop,
            "region": item.region,
            "language": item.language,
            "status": _value(item.status),
            "is_active": item.is_active,
            "publication_date": _value(item.publication_date),
            "retrieved_at": _value(item.retrieved_at),
            "page_count": item.page_count,
            "content_hash": item.content_hash,
        }
        for item, source in rows
    ]
    await _audit(session, current_user, "admin.documents_listed", "source_document")
    return result


@router.get("/ingestion")
async def list_ingestion(current_user: AdminUser, session: Session) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(IngestionJob, GovernmentSource, SourceDocument)
            .join(GovernmentSource, IngestionJob.government_source_id == GovernmentSource.id)
            .outerjoin(SourceDocument, IngestionJob.source_document_id == SourceDocument.id)
            .order_by(IngestionJob.created_at.desc())
            .limit(200)
        )
    ).all()
    result = [
        {
            "id": str(job.id),
            "source_name": source.name,
            "document_title": document.title if document else None,
            "status": _value(job.status),
            "trigger_type": _value(job.trigger_type),
            "started_at": _value(job.started_at),
            "completed_at": _value(job.completed_at),
            "chunks_processed": job.chunks_processed,
            "chunks_failed": job.chunks_failed,
            "error_summary": job.error_summary,
            "ingestion_version": job.ingestion_version,
        }
        for job, source, document in rows
    ]
    await _audit(session, current_user, "admin.ingestion_listed", "ingestion_job")
    return result


@router.get("/feedback")
async def list_feedback(current_user: AdminUser, session: Session) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(Feedback, User)
            .join(User, Feedback.user_id == User.id)
            .order_by(Feedback.created_at.desc())
            .limit(200)
        )
    ).all()
    result = [
        {
            "id": str(item.id),
            "user_id": str(user.id),
            "user_contact": user.email or user.phone_number,
            "rating": item.rating,
            "is_helpful": item.is_helpful,
            "comment": item.comment,
            "target": "message"
            if item.message_id
            else "image"
            if item.image_analysis_id
            else "faq"
            if item.faq_id
            else "general",
            "created_at": _value(item.created_at),
        }
        for item, user in rows
    ]
    await _audit(session, current_user, "admin.feedback_listed", "feedback")
    return result


@router.get("/image-analyses")
async def list_image_analyses(current_user: AdminUser, session: Session) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(ImageAnalysis, User)
            .join(User, ImageAnalysis.user_id == User.id)
            .order_by(ImageAnalysis.created_at.desc())
            .limit(200)
        )
    ).all()
    result = [
        {
            "id": str(item.id),
            "user_id": str(user.id),
            "user_contact": user.email or user.phone_number,
            "status": _value(item.status),
            "observed_symptoms": item.observed_symptoms,
            "possible_issue": item.possible_issue,
            "candidate_issues": item.candidate_issues,
            "quality_assessment": item.quality_assessment,
            "evidence": _safe_metadata(item.evidence_json),
            "error_code": item.error_code,
            "model_name": item.model_name,
            "processed_at": _value(item.processed_at),
            "created_at": _value(item.created_at),
        }
        for item, user in rows
    ]
    await _audit(session, current_user, "admin.image_analyses_listed", "image_analysis")
    return result


@router.get("/audit-logs")
async def list_audit_logs(current_user: AdminUser, session: Session) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(AuditLog, User)
            .outerjoin(User, AuditLog.actor_user_id == User.id)
            .order_by(AuditLog.created_at.desc())
            .limit(300)
        )
    ).all()
    result = [
        {
            "id": str(item.id),
            "actor_user_id": _value(item.actor_user_id),
            "actor_contact": (user.email or user.phone_number) if user else None,
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": _value(item.entity_id),
            "metadata": _safe_metadata(item.metadata_json),
            "created_at": _value(item.created_at),
        }
        for item, user in rows
    ]
    await _audit(session, current_user, "admin.audit_logs_listed", "audit_log")
    return result


@router.get("/system")
async def system_status(current_user: AdminUser, session: Session) -> dict[str, Any]:
    sources = list(await session.scalars(select(GovernmentSource).order_by(GovernmentSource.name)))
    result = {
        "status": "ok",
        "database": "connected",
        "sources": [
            {
                "id": str(source.id),
                "name": source.name,
                "organization": source.organization,
                "is_active": source.is_active,
                "trust_status": _value(source.trust_status),
                "last_verified_at": _value(source.last_verified_at),
            }
            for source in sources
        ],
    }
    await _audit(session, current_user, "admin.system_viewed", "system")
    return result
