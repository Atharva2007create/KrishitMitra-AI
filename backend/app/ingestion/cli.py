import argparse
import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

from app.core.settings import get_settings
from app.db.connection import SessionFactory
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.storage import GovernmentDocumentStore
from app.integrations.embeddings import GeminiEmbeddingProvider
from app.integrations.embeddings.credentials import resolve_gemini_api_key
from app.knowledge.types import DocumentDescriptor
from app.models.enums import TriggerType


def _descriptor(value: dict[str, Any]) -> DocumentDescriptor:
    publication = value.get("publication_date")
    return DocumentDescriptor(
        source_name=str(value["source_name"]),
        organization=str(value["organization"]),
        base_url=str(value["base_url"]),
        title=str(value["title"]),
        url=str(value["official_url"]),
        document_type=str(value["document_type"]),
        language=str(value.get("language", "en")),
        crop=str(value.get("crop", "PIGEONPEA")),
        region=str(value["region"]) if value.get("region") else None,
        publication_date=date.fromisoformat(str(publication)) if publication else None,
        version=str(value["version"]) if value.get("version") else None,
        topics=tuple(str(item) for item in value.get("topics", [])),
        metadata=dict(value.get("metadata", {})),
    )


async def run(inventory_path: Path, dry_run: bool, retry: bool) -> None:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    descriptors = [_descriptor(item) for item in inventory["documents"] if item.get("ingest", True)]
    if dry_run:
        for item in descriptors:
            print(f"VERIFIED CONFIG: {item.organization} | {item.title} | {item.url}")
        return
    settings = get_settings()
    embeddings = GeminiEmbeddingProvider(
        resolve_gemini_api_key(
            settings.gemini_api_key, settings.gemini_secret_arn, settings.aws_region
        ),
        settings.embedding_model,
        settings.embedding_dimension,
    )
    store = GovernmentDocumentStore(settings.aws_s3_bucket_documents, settings.aws_region)
    async with SessionFactory() as session:
        pipeline = IngestionPipeline(session, embeddings, store)
        trigger = TriggerType.RETRY if retry else TriggerType.CLI
        for item in descriptors:
            document, job, duplicate = await pipeline.ingest(item, trigger)
            print(
                json.dumps(
                    {
                        "document_id": str(document.id),
                        "job_id": str(job.id),
                        "duplicate": duplicate,
                    }
                )
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest verified official KrishiMitra knowledge")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.inventory, args.dry_run, args.retry))


if __name__ == "__main__":
    main()
