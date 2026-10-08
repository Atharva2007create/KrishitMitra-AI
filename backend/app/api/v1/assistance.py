from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.chat import _assert_owned_cycle
from app.core.settings import get_settings
from app.db.connection import get_db
from app.integrations.ai import AIProvider, GeminiAIProvider
from app.integrations.ai.base import AIProviderError
from app.integrations.embeddings import GeminiEmbeddingProvider
from app.integrations.embeddings.base import EmbeddingError, EmbeddingProvider
from app.integrations.embeddings.credentials import resolve_gemini_api_key
from app.models.entities import ChatSession, FaqItem, FarmerProfile, ProblemCategory
from app.models.enums import Language, SessionOrigin
from app.schemas.assistance import (
    AssistanceQuestion,
    AssistanceResponse,
    GuidedSessionCreate,
    GuidedSessionResponse,
)
from app.security.dependencies import FarmerUser
from app.services.assistance import GuidedAssistanceService, RateLimitExceeded
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/assistance", tags=["guided assistance"])
Session = Annotated[AsyncSession, Depends(get_db)]


def get_assistance_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    key = resolve_gemini_api_key(
        settings.gemini_api_key, settings.gemini_secret_arn, settings.aws_region
    )
    return GeminiEmbeddingProvider(key, settings.embedding_model, settings.embedding_dimension)


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    key = resolve_gemini_api_key(
        settings.gemini_api_key, settings.gemini_secret_arn, settings.aws_region
    )
    return GeminiAIProvider(
        key,
        settings.gemini_model,
        settings.gemini_temperature,
        settings.gemini_max_output_tokens,
        settings.ai_request_timeout,
        settings.ai_max_retries,
        settings.gemini_fallback_model,
    )


EmbeddingDependency = Annotated[EmbeddingProvider, Depends(get_assistance_embedding_provider)]
AIDependency = Annotated[AIProvider, Depends(get_ai_provider)]


@router.post("/sessions", response_model=GuidedSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_guided_session(
    payload: GuidedSessionCreate, current_user: FarmerUser, session: Session
) -> ChatSession:
    category = await session.scalar(
        select(ProblemCategory).where(
            ProblemCategory.id == payload.problem_category_id,
            ProblemCategory.is_active.is_(True),
        )
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if payload.crop_cycle_id is not None:
        await _assert_owned_cycle(session, current_user.id, payload.crop_cycle_id)
    if payload.selected_faq_id is not None:
        faq = await session.scalar(
            select(FaqItem).where(
                FaqItem.id == payload.selected_faq_id,
                FaqItem.problem_category_id == category.id,
                FaqItem.is_active.is_(True),
            )
        )
        if faq is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ not found")
    profile = await session.scalar(
        select(FarmerProfile).where(FarmerProfile.user_id == current_user.id)
    )
    language = payload.language or (profile.preferred_language if profile else None)
    chat = ChatSession(
        user_id=current_user.id,
        crop_cycle_id=payload.crop_cycle_id,
        problem_category_id=category.id,
        selected_faq_id=payload.selected_faq_id,
        origin_type=SessionOrigin.FAQ if payload.selected_faq_id else SessionOrigin.CATEGORY,
        language=language or Language.EN,
        title=category.display_name_en,
    )
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


@router.post("/sessions/{session_id}/questions", response_model=AssistanceResponse)
async def ask_personalized_question(
    session_id: UUID,
    payload: AssistanceQuestion,
    current_user: FarmerUser,
    session: Session,
    embeddings: EmbeddingDependency,
    ai: AIDependency,
) -> AssistanceResponse:
    settings = get_settings()
    service = GuidedAssistanceService(
        session, RetrievalService(session, embeddings, settings), ai, settings
    )
    try:
        return await service.answer(
            current_user,
            session_id,
            payload.question,
            payload.language,
            payload.attachment_ids,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except (AIProviderError, EmbeddingError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assistance service is temporarily unavailable; the question was preserved.",
        ) from exc
