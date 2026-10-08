from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import GovernmentSource, SourceDocument
from app.models.enums import RecordStatus, TrustStatus
from app.schemas.knowledge import PublicDocumentResponse, PublicSourceResponse, SourceDetailResponse
from app.security.dependencies import CurrentUser

router = APIRouter(prefix="/sources", tags=["government sources"])
Session = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[PublicSourceResponse])
async def list_sources(current_user: CurrentUser, session: Session) -> list[GovernmentSource]:
    del current_user
    return list(
        await session.scalars(
            select(GovernmentSource)
            .where(
                GovernmentSource.is_active.is_(True),
                GovernmentSource.trust_status == TrustStatus.APPROVED,
            )
            .order_by(GovernmentSource.name)
        )
    )


@router.get("/{source_id}", response_model=SourceDetailResponse)
async def get_source(
    source_id: UUID, current_user: CurrentUser, session: Session
) -> SourceDetailResponse:
    del current_user
    source = await session.scalar(
        select(GovernmentSource).where(
            GovernmentSource.id == source_id,
            GovernmentSource.is_active.is_(True),
            GovernmentSource.trust_status == TrustStatus.APPROVED,
        )
    )
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    documents = list(
        await session.scalars(
            select(SourceDocument)
            .where(
                SourceDocument.government_source_id == source.id,
                SourceDocument.is_active.is_(True),
                SourceDocument.status == RecordStatus.COMPLETED,
            )
            .order_by(SourceDocument.title)
        )
    )
    return SourceDetailResponse(
        id=source.id,
        name=source.name,
        organization=source.organization,
        base_url=source.base_url,
        source_type=source.source_type,
        trust_status=source.trust_status,
        last_verified_at=source.last_verified_at,
        documents=[
            PublicDocumentResponse(
                id=document.id,
                title=document.title,
                source_url=document.canonical_url or document.source_url,
                publication_date=document.publication_date,
                document_type=document.document_type,
                crop=document.crop,
                region=document.region,
                language=document.language,
                page_count=document.page_count,
                metadata=document.metadata_json,
            )
            for document in documents
        ],
    )
