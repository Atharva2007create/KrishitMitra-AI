from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.models.entities import GovernmentSource, KnowledgeChunk, SourceDocument
from app.models.enums import KnowledgeTopic, RecordStatus, TrustStatus
from app.services.retrieval import RetrievalService


class FixedEmbeddings:
    model = "test-embedding"
    dimension = 768

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * 767 for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0] + [0.0] * 767


@pytest.mark.asyncio
async def test_hybrid_retrieval_filters_and_citation_chain(session: AsyncSession) -> None:
    source = GovernmentSource(
        name="ICAR-IIPR Retrieval",
        organization="ICAR-Indian Institute of Pulses Research",
        base_url="https://www.icar-iipr.org.in",
        source_type="OFFICIAL_PUBLICATION",
        trust_status=TrustStatus.APPROVED,
        is_active=True,
    )
    session.add(source)
    await session.flush()
    document = SourceDocument(
        government_source_id=source.id,
        title="Official Sowing Guide",
        source_url="https://www.icar-iipr.org.in/sowing-guide",
        canonical_url="https://www.icar-iipr.org.in/sowing-guide",
        content_hash="d" * 64,
        document_type="HTML",
        crop="PIGEONPEA",
        language="en",
        status=RecordStatus.COMPLETED,
        is_active=True,
    )
    session.add(document)
    await session.flush()
    active = KnowledgeChunk(
        source_document_id=document.id,
        chunk_index=0,
        content="Pigeonpea sowing evidence with an exact official spacing reference.",
        content_hash="e" * 64,
        embedding=[1.0] + [0.0] * 767,
        embedding_model="test-embedding",
        embedding_dimension=768,
        embedding_created_at=datetime.now(UTC),
        crop="PIGEONPEA",
        topic=KnowledgeTopic.SOWING,
        language="en",
        page_start=4,
        page_end=4,
        section_title="Sowing",
        source_reference=document.canonical_url,
        ingestion_version="test-v1",
        is_active=True,
    )
    inactive = KnowledgeChunk(
        source_document_id=document.id,
        chunk_index=1,
        content="Superseded pigeonpea sowing evidence.",
        content_hash="f" * 64,
        embedding=[1.0] + [0.0] * 767,
        embedding_model="test-embedding",
        embedding_dimension=768,
        embedding_created_at=datetime.now(UTC),
        crop="PIGEONPEA",
        topic=KnowledgeTopic.SOWING,
        language="en",
        ingestion_version="old-v0",
        is_active=False,
    )
    session.add_all([active, inactive])
    await session.commit()
    settings = Settings(app_env="test", rag_min_relevance_threshold=0.1)
    service = RetrievalService(session, FixedEmbeddings(), settings)
    result = await service.retrieve_evidence("When should Tur sowing be done?", crop="Arhar")
    assert result.sufficient is True
    assert [item.chunk_id for item in result.results] == [active.id]
    assert result.results[0].citation.organization.startswith("ICAR-")
    assert result.results[0].citation.page_start == 4
    assert result.results[0].citation.source_url == document.canonical_url


@pytest.mark.asyncio
async def test_no_evidence_for_out_of_scope_query(session: AsyncSession) -> None:
    service = RetrievalService(session, FixedEmbeddings(), Settings(app_env="test"))
    result = await service.retrieve_evidence("How do I repair a tractor gearbox?")
    assert result.sufficient is False
    assert result.reason == "OUT_OF_SCOPE"
    assert result.results == []
