import hashlib
import re

from app.knowledge.types import ExtractedBlock

SPACE_RUN = re.compile(r"[ \t\f\v]+")
LINE_RUN = re.compile(r"\n{3,}")


def normalize_text(value: str) -> str:
    value = value.replace("\u00a0", " ").replace("\x00", "")
    lines = [SPACE_RUN.sub(" ", line).strip() for line in value.splitlines()]
    return LINE_RUN.sub("\n\n", "\n".join(line for line in lines if line)).strip()


def normalize_blocks(blocks: list[ExtractedBlock]) -> list[ExtractedBlock]:
    normalized: list[ExtractedBlock] = []
    seen: set[tuple[int | None, str]] = set()
    for block in blocks:
        text = normalize_text(block.text)
        identity = (block.page, text)
        if len(text) < 20 or identity in seen:
            continue
        seen.add(identity)
        normalized.append(
            ExtractedBlock(text=text, page=block.page, section=block.section, kind=block.kind)
        )
    return normalized


def knowledge_hash(blocks: list[ExtractedBlock]) -> str:
    canonical = "\n\n".join(
        f"page={block.page or ''}|section={block.section or ''}|kind={block.kind}\n{block.text}"
        for block in blocks
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
