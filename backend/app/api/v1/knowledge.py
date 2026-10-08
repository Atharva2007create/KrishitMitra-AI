from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.connection import get_db
from app.integrations.embeddings import GeminiEmbeddingProvider
from app.integrations.embeddings.base import EmbeddingError, EmbeddingProvider
from app.integrations.embeddings.credentials import resolve_gemini_api_key
from app.schemas.knowledge import (
    CitationResponse,
    EvidenceResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.security.dependencies import CurrentUser
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/knowledge", tags=["government knowledge"])
Session = Annotated[AsyncSession, Depends(get_db)]


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    return GeminiEmbeddingProvider(
        resolve_gemini_api_key(
            settings.gemini_api_key, settings.gemini_secret_arn, settings.aws_region
        ),
        settings.embedding_model,
        settings.embedding_dimension,
    )


EmbeddingDependency = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    current_user: CurrentUser,
    session: Session,
    embeddings: EmbeddingDependency,
) -> KnowledgeSearchResponse:
    del current_user
    try:
        result = await RetrievalService(session, embeddings, get_settings()).retrieve_evidence(
            query=payload.query,
            crop=payload.crop,
            topic=payload.topic,
            source_id=payload.source_id,
            region=payload.region,
            language=payload.language,
            limit=payload.limit,
        )
    except (EmbeddingError, ValueError) as exc:
        code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if isinstance(exc, EmbeddingError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return KnowledgeSearchResponse(
        query=result.query,
        crop=result.crop,
        sufficient=result.sufficient,
        reason=result.reason,
        results=[
            EvidenceResponse(
                chunk_id=item.chunk_id,
                content=item.content,
                score=item.score,
                vector_score=item.vector_score,
                lexical_score=item.lexical_score,
                topic=item.topic,
                source=CitationResponse(**item.citation.__dict__),
            )
            for item in result.results
        ],
    )
