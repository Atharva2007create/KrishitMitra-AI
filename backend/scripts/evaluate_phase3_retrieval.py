"""Run and persist the Phase 3 retrieval evaluation against an ingested corpus."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any


async def run(dataset_path: Path) -> None:
    from app.core.settings import get_settings
    from app.db.connection import SessionFactory, engine
    from app.integrations.embeddings import GeminiEmbeddingProvider
    from app.integrations.embeddings.credentials import resolve_gemini_api_key
    from app.services.retrieval import RetrievalService

    dataset: dict[str, Any] = json.loads(dataset_path.read_text(encoding="utf-8"))
    settings = get_settings()
    provider = GeminiEmbeddingProvider(
        resolve_gemini_api_key(
            settings.gemini_api_key, settings.gemini_secret_arn, settings.aws_region
        ),
        settings.embedding_model,
        settings.embedding_dimension,
    )
    passed = 0
    failed = 0
    async with SessionFactory() as session:
        service = RetrievalService(session, provider, settings)
        for item in dataset["questions"]:
            result = await service.retrieve_evidence(str(item["question"]), limit=5)
            citations = [evidence.citation.document_title for evidence in result.results]
            if item["expected_topic"] == "NO_EVIDENCE":
                success = not result.sufficient
            else:
                expected_document = item.get("expected_document")
                success = result.sufficient and (
                    expected_document is None or expected_document in citations
                )
            item["retrieved_result"] = {
                "sufficient": result.sufficient,
                "reason": result.reason,
                "chunk_ids": [str(evidence.chunk_id) for evidence in result.results],
                "documents": citations,
                "topics": [evidence.topic.value for evidence in result.results],
            }
            item["pass"] = success
            passed += int(success)
            failed += int(not success)
    dataset["status"] = "COMPLETED"
    dataset["summary"] = {"total": passed + failed, "passed": passed, "failed": failed}
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    await engine.dispose()
    print(json.dumps(dataset["summary"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.dataset))


if __name__ == "__main__":
    main()
