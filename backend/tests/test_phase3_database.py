from datetime import UTC, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import GovernmentSource, KnowledgeChunk, SourceDocument
from app.models.enums import KnowledgeTopic, RecordStatus, TrustStatus


async def _source_document(session: AsyncSession) -> tuple[GovernmentSource, SourceDocument]:
    source = GovernmentSource(
        name="ICAR-IIPR Test",
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
        title="Official Pigeonpea Test Fixture",
        source_url="https://www.icar-iipr.org.in/test-fixture",
        canonical_url="https://www.icar-iipr.org.in/test-fixture",
        content_hash="a" * 64,
        document_type="HTML",
        crop="PIGEONPEA",
        language="en",
        status=RecordStatus.COMPLETED,
        is_active=True,
    )
    session.add(document)
    await session.flush()
    return source, document


@pytest.mark.asyncio
async def test_pgvector_extension_dimension_and_indexes(session: AsyncSession) -> None:
    extension = await session.scalar(
        text("SELECT extname FROM pg_extension WHERE extname='vector'")
    )
    assert extension == "vector"
    vector_type = await session.scalar(
        text(
            "SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a "
            "JOIN pg_class c ON c.oid=a.attrelid "
            "WHERE c.relname='knowledge_chunks' AND a.attname='embedding'"
        )
    )
    assert vector_type == "vector(768)"
    indexes = set(
        await session.scalars(
            text("SELECT indexname FROM pg_indexes WHERE tablename='knowledge_chunks'")
        )
    )
    assert "ix_knowledge_chunks_embedding_hnsw" in indexes
    assert "ix_knowledge_chunks_search_vector" in indexes


@pytest.mark.asyncio
async def test_chunk_constraints_and_text_search(session: AsyncSession) -> None:
    _, document = await _source_document(session)
    chunk = KnowledgeChunk(
        source_document_id=document.id,
        chunk_index=0,
        content="Official pigeonpea sowing recommendation is preserved.",
        content_hash="b" * 64,
        embedding=[1.0] + [0.0] * 767,
        embedding_model="test-embedding",
        embedding_dimension=768,
        embedding_created_at=datetime.now(UTC),
        crop="PIGEONPEA",
        topic=KnowledgeTopic.SOWING,
        language="en",
        ingestion_version="test-v1",
        is_active=True,
    )
    session.add(chunk)
    await session.commit()
    match = await session.scalar(
        select(KnowledgeChunk.id).where(
            KnowledgeChunk.search_vector.op("@@")(text("websearch_to_tsquery('english', 'sowing')"))
        )
    )
    assert match == chunk.id

    invalid = KnowledgeChunk(
        source_document_id=document.id,
        chunk_index=1,
        content="invalid dimension",
        content_hash="c" * 64,
        embedding=[0.0] * 768,
        embedding_model="test",
        embedding_dimension=767,
        embedding_created_at=datetime.now(UTC),
        crop="PIGEONPEA",
        topic=KnowledgeTopic.OTHER,
        language="en",
        ingestion_version="test-v1",
        is_active=False,
    )
    session.add(invalid)
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
