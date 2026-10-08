from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import (
    FaqCitation,
    FaqItem,
    GovernmentSource,
    KnowledgeChunk,
    ProblemCategory,
    SourceDocument,
)
from app.models.enums import Language, RecordStatus, TrustStatus
from app.schemas.assistance import CategoryResponse, FaqCitationResponse, FaqResponse
from app.security.dependencies import CurrentUser

router = APIRouter(tags=["guided assistance"])
Session = Annotated[AsyncSession, Depends(get_db)]
LanguageQuery = Annotated[Language, Query()]


def _localized(category: ProblemCategory, language: Language) -> tuple[str, str]:
    suffix = language.value
    return (
        str(getattr(category, f"display_name_{suffix}")),
        str(getattr(category, f"description_{suffix}")),
    )


async def _category_response(
    session: AsyncSession, category: ProblemCategory, language: Language
) -> CategoryResponse:
    title, description = _localized(category, language)
    count = await session.scalar(
        select(func.count(FaqItem.id)).where(
            FaqItem.problem_category_id == category.id, FaqItem.is_active.is_(True)
        )
    )
    return CategoryResponse(
        id=category.id,
        code=category.code,
        slug=category.slug,
        title=title,
        description=description,
        icon_key=category.icon_key,
        display_order=category.display_order,
        requires_live_data=category.requires_live_data,
        faq_count=int(count or 0),
    )


async def _active_category(session: AsyncSession, slug: str) -> ProblemCategory:
    category = await session.scalar(
        select(ProblemCategory).where(
            ProblemCategory.slug == slug, ProblemCategory.is_active.is_(True)
        )
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


async def _faq_response(
    session: AsyncSession, faq: FaqItem, category: ProblemCategory, language: Language
) -> FaqResponse:
    rows = (
        await session.execute(
            select(FaqCitation, KnowledgeChunk, SourceDocument, GovernmentSource)
            .join(KnowledgeChunk, KnowledgeChunk.id == FaqCitation.knowledge_chunk_id)
            .join(SourceDocument, SourceDocument.id == FaqCitation.source_document_id)
            .join(GovernmentSource, GovernmentSource.id == SourceDocument.government_source_id)
            .where(
                FaqCitation.faq_id == faq.id,
                KnowledgeChunk.is_active.is_(True),
                SourceDocument.is_active.is_(True),
                SourceDocument.status == RecordStatus.COMPLETED,
                GovernmentSource.is_active.is_(True),
                GovernmentSource.trust_status == TrustStatus.APPROVED,
            )
            .order_by(FaqCitation.citation_order)
        )
    ).all()
    citations = [
        FaqCitationResponse(
            organization=source.organization,
            document_title=document.title,
            source_url=document.canonical_url or document.source_url,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            section=chunk.section_title,
        )
        for _, chunk, document, source in rows
    ]
    if not citations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="FAQ evidence is no longer active",
        )
    suffix = language.value
    return FaqResponse(
        id=faq.id,
        category_slug=category.slug,
        question=str(getattr(faq, f"question_{suffix}")),
        answer=str(getattr(faq, f"answer_{suffix}")),
        language=language,
        evidence_status=faq.evidence_status,
        citations=citations,
    )


@router.get("/problem-categories", response_model=list[CategoryResponse])
async def list_problem_categories(
    current_user: CurrentUser,
    session: Session,
    language: LanguageQuery = Language.EN,
) -> list[CategoryResponse]:
    del current_user
    categories = list(
        await session.scalars(
            select(ProblemCategory)
            .where(ProblemCategory.is_active.is_(True))
            .order_by(ProblemCategory.display_order)
        )
    )
    return [await _category_response(session, item, language) for item in categories]


@router.get("/problem-categories/{slug}", response_model=CategoryResponse)
async def get_problem_category(
    slug: str,
    current_user: CurrentUser,
    session: Session,
    language: LanguageQuery = Language.EN,
) -> CategoryResponse:
    del current_user
    return await _category_response(session, await _active_category(session, slug), language)


@router.get("/problem-categories/{slug}/faqs", response_model=list[FaqResponse])
async def list_category_faqs(
    slug: str,
    current_user: CurrentUser,
    session: Session,
    language: LanguageQuery = Language.EN,
) -> list[FaqResponse]:
    del current_user
    category = await _active_category(session, slug)
    faqs = list(
        await session.scalars(
            select(FaqItem)
            .where(FaqItem.problem_category_id == category.id, FaqItem.is_active.is_(True))
            .order_by(FaqItem.display_order)
        )
    )
    return [await _faq_response(session, faq, category, language) for faq in faqs]


@router.get("/faqs/{faq_id}", response_model=FaqResponse)
async def get_faq(
    faq_id: UUID,
    current_user: CurrentUser,
    session: Session,
    language: LanguageQuery = Language.EN,
) -> FaqResponse:
    del current_user
    row = (
        await session.execute(
            select(FaqItem, ProblemCategory)
            .join(ProblemCategory, ProblemCategory.id == FaqItem.problem_category_id)
            .where(
                FaqItem.id == faq_id,
                FaqItem.is_active.is_(True),
                ProblemCategory.is_active.is_(True),
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ not found")
    return await _faq_response(session, row[0], row[1], language)
