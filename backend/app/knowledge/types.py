from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.models.enums import KnowledgeTopic


@dataclass(frozen=True)
class ExtractedBlock:
    text: str
    page: int | None = None
    section: str | None = None
    kind: str = "paragraph"


@dataclass(frozen=True)
class ChunkDraft:
    index: int
    content: str
    content_hash: str
    topic: KnowledgeTopic
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    requires_regulatory_validation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentDescriptor:
    source_name: str
    organization: str
    base_url: str
    title: str
    url: str
    document_type: str
    language: str = "en"
    crop: str = "PIGEONPEA"
    region: str | None = "India"
    publication_date: date | None = None
    version: str | None = None
    topics: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
