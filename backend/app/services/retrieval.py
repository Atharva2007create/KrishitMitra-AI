import logging
from dataclasses import dataclass
from datetime import date
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.ingestion.taxonomy import infer_topic, normalize_crop
from app.integrations.embeddings.base import EmbeddingProvider
from app.models.entities import GovernmentSource, KnowledgeChunk, SourceDocument
from app.models.enums import KnowledgeTopic, RecordStatus, TrustStatus

logger = logging.getLogger(__name__)
UNSUPPORTED_TERMS = {
    "coffee",
    "tractor gearbox",
    "live weather",
    "today's weather",
    "mandi price",
    "market price",
    "bitcoin",
    "laptop repair",
}


@dataclass(frozen=True)
class Citation:
    organization: str
    document_title: str
    source_url: str | None
    publication_date: date | None
    page_start: int | None
    page_end: int | None
    section: str | None
    ingestion_version: str


@dataclass(frozen=True)
class Evidence:
    chunk_id: UUID
    content: str
    score: float
    vector_score: float
    lexical_score: float
    topic: KnowledgeTopic
    citation: Citation


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    crop: str
    sufficient: bool
    reason: str | None
    results: list[Evidence]


class RetrievalService:
    def __init__(
        self, session: AsyncSession, embeddings: EmbeddingProvider, settings: Settings
    ) -> None:
        self.session = session
        self.embeddings = embeddings
        self.settings = settings

    def _base_query(
        self,
        query_vector: list[float],
        query: str,
        crop: str,
        topic: KnowledgeTopic | None,
        source_id: UUID | None,
        region: str | None,
        language: str | None,
    ) -> Select[Any]:
        distance = KnowledgeChunk.embedding.cosine_distance(query_vector)
        vector_score = func.greatest(0.0, 1.0 - distance).label("vector_score")
        lexical_score = func.ts_rank_cd(
            KnowledgeChunk.search_vector, func.websearch_to_tsquery("english", query)
        ).label("lexical_score")
        combined = (
            self.settings.rag_vector_weight * vector_score
            + self.settings.rag_lexical_weight * func.least(lexical_score, 1.0)
        ).label("combined_score")
        statement = (
            select(
                KnowledgeChunk,
                SourceDocument,
                GovernmentSource,
                vector_score,
                lexical_score,
                combined,
            )
            .join(SourceDocument, SourceDocument.id == KnowledgeChunk.source_document_id)
            .join(GovernmentSource, GovernmentSource.id == SourceDocument.government_source_id)
            .where(
                KnowledgeChunk.is_active.is_(True),
                SourceDocument.is_active.is_(True),
                SourceDocument.status == RecordStatus.COMPLETED,
                GovernmentSource.is_active.is_(True),
                GovernmentSource.trust_status == TrustStatus.APPROVED,
                KnowledgeChunk.crop == crop,
            )
        )
        if topic is not None:
            statement = statement.where(KnowledgeChunk.topic == topic)
        if source_id is not None:
            statement = statement.where(GovernmentSource.id == source_id)
        if region is not None:
            statement = statement.where(KnowledgeChunk.region == region)
        if language is not None:
            statement = statement.where(KnowledgeChunk.language == language)
        return statement.order_by(combined.desc()).limit(self.settings.rag_max_top_k * 3)

    async def retrieve_evidence(
        self,
        query: str,
        crop: str = "tur",
        topic: KnowledgeTopic | None = None,
        source_id: UUID | None = None,
        region: str | None = None,
        language: str | None = None,
        limit: int | None = None,
    ) -> RetrievalResult:
        started = perf_counter()
        cleaned = " ".join(query.split())
        normalized_crop = normalize_crop(crop)
        lowered = cleaned.lower()
        if not cleaned or any(term in lowered for term in UNSUPPORTED_TERMS):
            return RetrievalResult(cleaned, normalized_crop, False, "OUT_OF_SCOPE", [])
        inferred_topic = infer_topic(cleaned)
        query_vector = await self.embeddings.embed_query(cleaned)
        requested_limit = min(limit or self.settings.rag_default_top_k, self.settings.rag_max_top_k)
        rows = (
            await self.session.execute(
                self._base_query(
                    query_vector,
                    cleaned,
                    normalized_crop,
                    topic,
                    source_id,
                    region,
                    language,
                )
            )
        ).all()
        evidence: list[Evidence] = []
        for chunk, document, source, vector_score, lexical_score, score in rows:
            numeric_score = float(score)
            if numeric_score < self.settings.rag_min_relevance_threshold:
                continue
            evidence.append(
                Evidence(
                    chunk_id=chunk.id,
                    content=chunk.content,
                    score=numeric_score,
                    vector_score=float(vector_score),
                    lexical_score=float(lexical_score),
                    topic=chunk.topic,
                    citation=Citation(
                        organization=source.organization,
                        document_title=document.title,
                        source_url=document.canonical_url or document.source_url,
                        publication_date=document.publication_date,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        section=chunk.section_title,
                        ingestion_version=chunk.ingestion_version,
                    ),
                )
            )
            if len(evidence) >= requested_limit:
                break
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        logger.info(
            "knowledge_retrieval",
            extra={
                "retrieval_latency_ms": elapsed_ms,
                "retrieval_result_count": len(evidence),
                "retrieval_no_result": not evidence,
                "inferred_topic": inferred_topic.value,
            },
        )
        return RetrievalResult(
            cleaned,
            normalized_crop,
            bool(evidence),
            None if evidence else "INSUFFICIENT_EVIDENCE",
            evidence,
        )
