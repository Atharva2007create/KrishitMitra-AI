from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.acquisition import AcquiredDocument
from app.ingestion.pipeline import IngestionPipeline
from app.knowledge.types import DocumentDescriptor
from app.models.entities import KnowledgeChunk, SourceDocument


class FixedEmbeddings:
    model = "test-embedding"
    dimension = 768

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * 767 for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0] + [0.0] * 767


class MemoryStore:
    def __init__(self) -> None:
        self.originals: dict[str, bytes] = {}
        self.processed: dict[str, dict[str, Any]] = {}

    async def put_original(self, key: str, content: bytes, mime_type: str, checksum: str) -> None:
        self.originals[key] = content

    async def put_processed(self, key: str, payload: dict[str, Any]) -> None:
        self.processed[key] = payload


@pytest.mark.asyncio
async def test_duplicate_ingestion_is_idempotent(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    stable_content = (
        b"<html><body><main><h2>Sowing</h2><p>Pigeonpea sowing evidence "
        b"at 20 kg/ha and 120 x 60 cm spacing.</p>"
    )
    calls = 0

    async def fixed_acquire(url: str) -> AcquiredDocument:
        nonlocal calls
        calls += 1
        dynamic = f"<script>request={calls}</script></main></body></html>".encode()
        return AcquiredDocument(
            canonical_url="https://www.icar-iipr.org.in/fixture",
            content=stable_content + dynamic,
            mime_type="text/html",
            checksum=str(calls) * 64,
        )

    monkeypatch.setattr("app.ingestion.pipeline.acquire", fixed_acquire)
    store = MemoryStore()
    pipeline = IngestionPipeline(session, FixedEmbeddings(), store)  # type: ignore[arg-type]
    descriptor = DocumentDescriptor(
        source_name="ICAR-IIPR Pipeline Test",
        organization="ICAR-Indian Institute of Pulses Research",
        base_url="https://www.icar-iipr.org.in",
        title="Official Fixture",
        url="https://www.icar-iipr.org.in/fixture",
        document_type="HTML",
    )
    first, _, first_duplicate = await pipeline.ingest(descriptor)
    second, _, second_duplicate = await pipeline.ingest(descriptor)
    assert first_duplicate is False
    assert second_duplicate is True
    assert first.id == second.id
    assert await session.scalar(select(func.count()).select_from(SourceDocument)) == 1
    assert await session.scalar(select(func.count()).select_from(KnowledgeChunk)) == 1
    assert len(store.originals) == 1
