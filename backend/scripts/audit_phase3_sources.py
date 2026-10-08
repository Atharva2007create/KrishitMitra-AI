"""Audit live Phase 3 official sources without changing S3 or PostgreSQL."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.ingestion.acquisition import acquire
from app.ingestion.chunking import chunk_blocks
from app.ingestion.extraction import extract
from app.ingestion.normalization import knowledge_hash, normalize_blocks
from app.ingestion.taxonomy import contains_any_term


async def audit_document(item: dict[str, Any]) -> dict[str, Any]:
    acquired = await acquire(str(item["official_url"]))
    blocks, page_count = extract(acquired.content, acquired.mime_type)
    blocks = normalize_blocks(blocks)
    include_terms = [
        str(term).lower() for term in item.get("metadata", {}).get("block_include_terms", [])
    ]
    if include_terms:
        blocks = [
            block
            for block in blocks
            if contains_any_term(f"{block.section or ''} {block.text}", include_terms)
        ]
    chunks = chunk_blocks(blocks)
    if not chunks:
        raise RuntimeError("Live official document produced zero relevant chunks")
    return {
        "title": item["title"],
        "canonical_url": acquired.canonical_url,
        "mime_type": acquired.mime_type,
        "sha256": acquired.checksum,
        "knowledge_sha256": knowledge_hash(blocks),
        "bytes": len(acquired.content),
        "pages": page_count,
        "blocks": len(blocks),
        "candidate_chunks": len(chunks),
        "topics": sorted({chunk.topic.value for chunk in chunks}),
    }


async def run(path: Path) -> None:
    inventory = json.loads(path.read_text(encoding="utf-8"))
    results = []
    for item in inventory["documents"]:
        try:
            results.append({"status": "PASS", **(await audit_document(item))})
        except Exception as exc:
            results.append(
                {
                    "status": "FAIL",
                    "title": item["title"],
                    "official_url": item["official_url"],
                    "error": f"{type(exc).__name__}: {exc}"[:500],
                }
            )
    print(json.dumps({"documents": results}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.inventory))


if __name__ == "__main__":
    main()
