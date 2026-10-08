import logging
from datetime import UTC, datetime
from pathlib import PurePosixPath
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.acquisition import acquire
from app.ingestion.chunking import chunk_blocks
from app.ingestion.extraction import extract
from app.ingestion.normalization import knowledge_hash, normalize_blocks
from app.ingestion.storage import GovernmentDocumentStore
from app.ingestion.taxonomy import contains_any_term, normalize_crop
from app.integrations.embeddings.base import EmbeddingProvider, validate_vectors
from app.knowledge.types import DocumentDescriptor
from app.models.entities import GovernmentSource, IngestionJob, KnowledgeChunk, SourceDocument
from app.models.enums import IngestionStatus, RecordStatus, TriggerType, TrustStatus

logger = logging.getLogger(__name__)


class IngestionError(RuntimeError):
    pass


class IngestionPipeline:
    def __init__(
        self,
        session: AsyncSession,
        embeddings: EmbeddingProvider,
        store: GovernmentDocumentStore,
        ingestion_version: str = "phase3-v1",
    ) -> None:
        self.session = session
        self.embeddings = embeddings
        self.store = store
        self.ingestion_version = ingestion_version

    async def _source(self, item: DocumentDescriptor) -> GovernmentSource:
        source = await self.session.scalar(
            select(GovernmentSource).where(GovernmentSource.name == item.source_name)
        )
        if source is None:
            source = GovernmentSource(
                name=item.source_name,
                organization=item.organization,
                base_url=item.base_url,
                source_type="OFFICIAL_PUBLICATION",
                trust_status=TrustStatus.APPROVED,
                is_active=True,
                last_verified_at=datetime.now(UTC),
                notes="Official ICAR/ICAR-IIPR public source verified for Phase 3.",
            )
            self.session.add(source)
            await self.session.flush()
        return source

    async def ingest(
        self, item: DocumentDescriptor, trigger: TriggerType = TriggerType.CLI
    ) -> tuple[SourceDocument, IngestionJob, bool]:
        source = await self._source(item)
        job = IngestionJob(
            government_source_id=source.id,
            status=IngestionStatus.FETCHING,
            trigger_type=trigger,
            started_at=datetime.now(UTC),
            ingestion_version=self.ingestion_version,
            metadata_json={"source_url": item.url},
        )
        self.session.add(job)
        await self.session.commit()
        job_id = job.id
        source_id = source.id
        logger.info("ingestion_start", extra={"job_id": str(job_id), "source_id": str(source_id)})
        try:
            acquired = await acquire(item.url)
            duplicate = await self.session.scalar(
                select(SourceDocument).where(
                    SourceDocument.government_source_id == source.id,
                    SourceDocument.content_hash == acquired.checksum,
                )
            )
            if duplicate is not None:
                job.source_document_id = duplicate.id
                job.status = IngestionStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                job.metadata_json = {"duplicate": True, "checksum": acquired.checksum}
                await self.session.commit()
                return duplicate, job, True

            job.status = IngestionStatus.PROCESSING
            blocks, page_count = extract(acquired.content, acquired.mime_type)
            blocks = normalize_blocks(blocks)
            include_terms = [
                str(term).lower() for term in item.metadata.get("block_include_terms", [])
            ]
            if include_terms:
                blocks = [
                    block
                    for block in blocks
                    if contains_any_term(f"{block.section or ''} {block.text}", include_terms)
                ]
            chunks = chunk_blocks(blocks)
            if not chunks:
                raise IngestionError("Document produced zero valid chunks")
            normalized_hash = knowledge_hash(blocks)
            duplicate = await self.session.scalar(
                select(SourceDocument).where(
                    SourceDocument.government_source_id == source.id,
                    SourceDocument.canonical_url == acquired.canonical_url,
                    SourceDocument.metadata_json["knowledge_hash"].as_string() == normalized_hash,
                )
            )
            if duplicate is not None:
                job.source_document_id = duplicate.id
                job.status = IngestionStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                job.metadata_json = {
                    "duplicate": True,
                    "checksum": acquired.checksum,
                    "knowledge_hash": normalized_hash,
                }
                await self.session.commit()
                return duplicate, job, True

            previous = await self.session.scalar(
                select(SourceDocument)
                .where(
                    SourceDocument.government_source_id == source.id,
                    SourceDocument.canonical_url == acquired.canonical_url,
                    SourceDocument.is_active.is_(True),
                )
                .order_by(SourceDocument.created_at.desc())
            )
            document_id = uuid4()
            extension = ".pdf" if acquired.mime_type == "application/pdf" else ".html"
            organization_key = "icar-iipr" if "iipr" in source.name.lower() else "icar"
            original_key = str(
                PurePosixPath(
                    "government",
                    organization_key,
                    "pigeonpea",
                    str(document_id),
                    f"original{extension}",
                )
            )
            await self.store.put_original(
                original_key, acquired.content, acquired.mime_type, acquired.checksum
            )
            document = SourceDocument(
                id=document_id,
                government_source_id=source.id,
                title=item.title,
                source_url=item.url,
                canonical_url=acquired.canonical_url,
                s3_key=original_key,
                mime_type=acquired.mime_type,
                publication_date=item.publication_date,
                version=item.version or acquired.checksum[:12],
                document_type=item.document_type,
                crop=normalize_crop(item.crop),
                region=item.region,
                language=item.language,
                retrieved_at=datetime.now(UTC),
                content_hash=acquired.checksum,
                page_count=page_count,
                metadata_json={
                    **item.metadata,
                    "declared_topics": list(item.topics),
                    "knowledge_hash": normalized_hash,
                },
                is_active=False,
                supersedes_document_id=previous.id if previous else None,
                status=RecordStatus.PROCESSING,
            )
            self.session.add(document)
            await self.session.flush()
            job.source_document_id = document.id
            job.status = IngestionStatus.EMBEDDING
            vectors: list[list[float]] = []
            for start in range(0, len(chunks), 20):
                batch = chunks[start : start + 20]
                vectors.extend(
                    await self.embeddings.embed_documents([chunk.content for chunk in batch])
                )
            validate_vectors(vectors, len(chunks), self.embeddings.dimension)
            embedded_at = datetime.now(UTC)
            for chunk, vector in zip(chunks, vectors, strict=True):
                self.session.add(
                    KnowledgeChunk(
                        source_document_id=document.id,
                        chunk_index=chunk.index,
                        content=chunk.content,
                        content_hash=chunk.content_hash,
                        embedding=vector,
                        embedding_model=self.embeddings.model,
                        embedding_dimension=self.embeddings.dimension,
                        embedding_created_at=embedded_at,
                        crop=document.crop or "PIGEONPEA",
                        topic=chunk.topic,
                        region=document.region,
                        language=document.language or "en",
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        section_title=chunk.section_title,
                        source_reference=document.canonical_url,
                        publication_date=document.publication_date,
                        ingestion_version=self.ingestion_version,
                        requires_regulatory_validation=chunk.requires_regulatory_validation,
                        metadata_json=chunk.metadata,
                        is_active=True,
                    )
                )
            await self.store.put_processed(
                str(PurePosixPath("processed", str(document.id), "extracted.json")),
                {
                    "document_id": str(document.id),
                    "checksum": acquired.checksum,
                    "blocks": [
                        {
                            "page": block.page,
                            "section": block.section,
                            "kind": block.kind,
                            "text": block.text,
                        }
                        for block in blocks
                    ],
                },
            )
            if previous:
                previous.is_active = False
                await self.session.execute(
                    update(KnowledgeChunk)
                    .where(KnowledgeChunk.source_document_id == previous.id)
                    .values(is_active=False)
                )
            document.is_active = True
            document.status = RecordStatus.COMPLETED
            job.status = IngestionStatus.COMPLETED
            job.completed_at = datetime.now(UTC)
            job.chunks_processed = len(chunks)
            job.metadata_json = {
                "checksum": acquired.checksum,
                "page_count": page_count,
                "knowledge_hash": normalized_hash,
            }
            await self.session.commit()
            logger.info(
                "ingestion_complete",
                extra={
                    "job_id": str(job.id),
                    "document_id": str(document.id),
                    "chunks_created": len(chunks),
                },
            )
            return document, job, False
        except Exception as exc:
            await self.session.rollback()
            persisted_job = await self.session.get(IngestionJob, job_id)
            if persisted_job is not None:
                persisted_job.status = IngestionStatus.FAILED
                persisted_job.completed_at = datetime.now(UTC)
                persisted_job.error_summary = f"{type(exc).__name__}: ingestion failed"[:1000]
                await self.session.commit()
            logger.exception(
                "ingestion_failure",
                extra={"job_id": str(job_id), "failure_category": type(exc).__name__},
            )
            raise
