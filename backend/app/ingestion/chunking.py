import hashlib

from app.ingestion.taxonomy import infer_topic, requires_regulatory_validation
from app.knowledge.types import ChunkDraft, ExtractedBlock


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_blocks(
    blocks: list[ExtractedBlock], target_words: int = 600, overlap_words: int = 75
) -> list[ChunkDraft]:
    if target_words < 100 or overlap_words < 0 or overlap_words >= target_words:
        raise ValueError("Invalid chunk sizing")
    groups: list[list[ExtractedBlock]] = []
    current: list[ExtractedBlock] = []
    current_words = 0
    for block in blocks:
        block_words = _word_count(block.text)
        section_boundary = bool(current and block.section != current[-1].section)
        size_boundary = bool(current and current_words + block_words > target_words)
        boundary = section_boundary or size_boundary
        if boundary:
            groups.append(current)
            carry_text = (
                " ".join(item.text for item in current).split()[-overlap_words:]
                if size_boundary and not section_boundary
                else []
            )
            current = (
                [
                    ExtractedBlock(
                        text=" ".join(carry_text),
                        page=current[-1].page,
                        section=current[-1].section,
                    )
                ]
                if carry_text
                else []
            )
            current_words = len(carry_text)
        current.append(block)
        current_words += block_words
    if current:
        groups.append(current)

    chunks: list[ChunkDraft] = []
    seen_hashes: set[str] = set()
    for group in groups:
        content = "\n\n".join(item.text for item in group).strip()
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if not content or digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        pages = [item.page for item in group if item.page is not None]
        section = next((item.section for item in group if item.section), None)
        chunks.append(
            ChunkDraft(
                index=len(chunks),
                content=content,
                content_hash=digest,
                topic=infer_topic(content, section),
                page_start=min(pages) if pages else None,
                page_end=max(pages) if pages else None,
                section_title=section,
                requires_regulatory_validation=requires_regulatory_validation(content),
                metadata={"block_kinds": sorted({item.kind for item in group})},
            )
        )
    return chunks
