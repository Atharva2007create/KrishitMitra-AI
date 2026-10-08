from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.enums import KnowledgeTopic, TrustStatus

Query = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=1000)]


class KnowledgeSearchRequest(BaseModel):
    query: Query
    crop: str = "tur"
    topic: KnowledgeTopic | None = None
    source_id: UUID | None = None
    region: str | None = None
    language: str | None = None
    limit: int | None = Field(default=None, ge=1, le=20)


class CitationResponse(BaseModel):
    organization: str
    document_title: str
    source_url: str | None
    publication_date: date | None
    page_start: int | None
    page_end: int | None
    section: str | None
    ingestion_version: str


class EvidenceResponse(BaseModel):
    chunk_id: UUID
    content: str
    score: float
    vector_score: float
    lexical_score: float
    topic: KnowledgeTopic
    source: CitationResponse


class KnowledgeSearchResponse(BaseModel):
    query: str
    crop: str
    sufficient: bool
    reason: str | None
    results: list[EvidenceResponse]


class PublicSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    organization: str
    base_url: str | None
    source_type: str
    trust_status: TrustStatus
    last_verified_at: datetime | None


class PublicDocumentResponse(BaseModel):
    id: UUID
    title: str
    source_url: str | None
    publication_date: date | None
    document_type: str | None
    crop: str | None
    region: str | None
    language: str | None
    page_count: int | None
    metadata: dict[str, Any] | None = None


class SourceDetailResponse(PublicSourceResponse):
    documents: list[PublicDocumentResponse]
