from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.enums import (
    AttachmentSource,
    AttachmentStatus,
    AttachmentType,
    EvidenceStatus,
    Language,
)


class CategoryResponse(BaseModel):
    id: UUID
    code: str
    slug: str
    title: str
    description: str
    icon_key: str | None
    display_order: int
    requires_live_data: bool
    faq_count: int = 0


class FaqCitationResponse(BaseModel):
    organization: str
    document_title: str
    source_url: str | None
    page_start: int | None
    page_end: int | None
    section: str | None


class FaqResponse(BaseModel):
    id: UUID
    category_slug: str
    question: str
    answer: str
    language: Language
    evidence_status: EvidenceStatus
    citations: list[FaqCitationResponse]


class GuidedSessionCreate(BaseModel):
    problem_category_id: UUID
    crop_cycle_id: UUID | None = None
    selected_faq_id: UUID | None = None
    language: Language | None = None


class GuidedSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    problem_category_id: UUID
    crop_cycle_id: UUID | None
    selected_faq_id: UUID | None
    language: Language
    created_at: datetime


QuestionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AssistanceQuestion(BaseModel):
    question: QuestionText
    language: Language | None = None
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=5)

    @field_validator("question")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(ord(char) < 32 and char not in "\n\t" for char in value):
            raise ValueError("Question contains invalid control characters")
        return value


class AssistanceCategory(BaseModel):
    code: str
    title: str


class AssistanceResponse(BaseModel):
    message_id: UUID
    session_id: UUID
    category: AssistanceCategory
    answer: str
    language: Language
    intent: str
    evidence_status: EvidenceStatus
    citations: list[FaqCitationResponse]
    requires_follow_up: bool = False
    attachment_recommended: bool = False
    requires_live_data: bool = False
    requires_regulatory_validation: bool = False
    safety_flags: list[str] = Field(default_factory=list)
    live_data: list[dict[str, object]] = Field(default_factory=list)
    data_timestamp: datetime | None = None
    created_at: datetime


class AttachmentUploadRequest(BaseModel):
    chat_session_id: UUID
    attachment_type: AttachmentType
    source_type: AttachmentSource = AttachmentSource.UPLOAD
    file_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    mime_type: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    file_size: int = Field(gt=0)


class AttachmentUploadResponse(BaseModel):
    attachment_id: UUID
    analysis_id: UUID | None = None
    upload_url: str
    method: str = "POST"
    form_fields: dict[str, str]
    mime_type: str
    max_size_bytes: int
    expires_in_seconds: int


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_session_id: UUID
    message_id: UUID | None
    attachment_type: AttachmentType
    source_type: AttachmentSource
    file_name: str
    mime_type: str
    file_size: int | None
    status: AttachmentStatus
    created_at: datetime


class ImageAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    attachment_id: UUID | None
    status: str
    content_hash: str | None
    model_name: str | None
    observed_symptoms: dict[str, object] | None
    candidate_issues: list[dict[str, object]] | None
    quality_assessment: dict[str, object] | None
    evidence_json: dict[str, object] | None
    error_code: str | None
    processed_at: datetime | None
    created_at: datetime
