from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AreaUnit,
    AttachmentSource,
    AttachmentStatus,
    AttachmentType,
    CropCycleStatus,
    EvidenceStatus,
    IngestionStatus,
    KnowledgeTopic,
    Language,
    RecordStatus,
    SenderType,
    SessionOrigin,
    TriggerType,
    TrustStatus,
    UserRole,
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    cognito_sub: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(32), unique=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    farmer_profile: Mapped["FarmerProfile | None"] = relationship(back_populates="user")


class FarmerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "farmer_profiles"
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    preferred_language: Mapped[Language] = mapped_column(
        Enum(Language, name="language"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    taluka: Mapped[str] = mapped_column(String(100), nullable=False)
    village: Mapped[str | None] = mapped_column(String(120))
    user: Mapped[User] = relationship(back_populates="farmer_profile")
    farms: Mapped[list["Farm"]] = relationship(back_populates="farmer_profile")


class Farm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "farms"
    __table_args__ = (
        CheckConstraint("area_value > 0", name="area_positive"),
        Index("ix_farms_farmer_profile_id", "farmer_profile_id"),
    )
    farmer_profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("farmer_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(120))
    area_value: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    area_unit: Mapped[AreaUnit] = mapped_column(Enum(AreaUnit, name="area_unit"), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    taluka: Mapped[str] = mapped_column(String(100), nullable=False)
    village: Mapped[str | None] = mapped_column(String(120))
    soil_type: Mapped[str | None] = mapped_column(String(100))
    irrigation_type: Mapped[str | None] = mapped_column(String(100))
    farmer_profile: Mapped[FarmerProfile] = relationship(back_populates="farms")
    crop_cycles: Mapped[list["CropCycle"]] = relationship(back_populates="farm")


class CropCycle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crop_cycles"
    __table_args__ = (
        CheckConstraint("crop_name IN ('TUR', 'PIGEONPEA')", name="supported_crop"),
        CheckConstraint(
            "expected_harvest_date IS NULL OR expected_harvest_date >= sowing_date",
            name="expected_harvest_after_sowing",
        ),
        CheckConstraint(
            "actual_harvest_date IS NULL OR actual_harvest_date >= sowing_date",
            name="actual_harvest_after_sowing",
        ),
        Index("ix_crop_cycles_farm_id", "farm_id"),
    )
    farm_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("farms.id", ondelete="RESTRICT"), nullable=False
    )
    crop_name: Mapped[str] = mapped_column(String(32), nullable=False, default="TUR")
    crop_variety: Mapped[str | None] = mapped_column(String(120))
    sowing_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date)
    actual_harvest_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[CropCycleStatus] = mapped_column(
        Enum(CropCycleStatus, name="crop_cycle_status"), nullable=False
    )
    estimated_crop_stage: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    farm: Mapped[Farm] = relationship(back_populates="crop_cycles")


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (Index("ix_chat_sessions_user_id", "user_id"),)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    crop_cycle_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("crop_cycles.id", ondelete="SET NULL")
    )
    problem_category_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("problem_categories.id", ondelete="SET NULL")
    )
    selected_faq_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("faq_items.id", ondelete="SET NULL")
    )
    origin_type: Mapped[SessionOrigin] = mapped_column(
        Enum(SessionOrigin, name="session_origin"), default=SessionOrigin.DIRECT, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(200))
    language: Mapped[Language] = mapped_column(Enum(Language, name="chat_language"), nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Message(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_chat_session_id", "chat_session_id"),)
    chat_session_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("chat_sessions.id", ondelete="RESTRICT"), nullable=False
    )
    sender_type: Mapped[SenderType] = mapped_column(
        Enum(SenderType, name="sender_type"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language | None] = mapped_column(Enum(Language, name="message_language"))
    intent: Mapped[str | None] = mapped_column(String(80))
    evidence_status: Mapped[EvidenceStatus | None] = mapped_column(
        Enum(EvidenceStatus, name="evidence_status")
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProblemCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "problem_categories"
    __table_args__ = (Index("ix_problem_categories_active_order", "is_active", "display_order"),)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    display_name_hi: Mapped[str] = mapped_column(String(160), nullable=False)
    display_name_mr: Mapped[str] = mapped_column(String(160), nullable=False)
    description_en: Mapped[str] = mapped_column(String(500), nullable=False)
    description_hi: Mapped[str] = mapped_column(String(500), nullable=False)
    description_mr: Mapped[str] = mapped_column(String(500), nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(80))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_live_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class FaqItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "faq_items"
    __table_args__ = (
        Index(
            "ix_faq_items_category_active_order",
            "problem_category_id",
            "is_active",
            "display_order",
        ),
    )
    problem_category_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("problem_categories.id", ondelete="RESTRICT"), nullable=False
    )
    canonical_question: Mapped[str] = mapped_column(Text, nullable=False)
    question_en: Mapped[str] = mapped_column(Text, nullable=False)
    question_hi: Mapped[str] = mapped_column(Text, nullable=False)
    question_mr: Mapped[str] = mapped_column(Text, nullable=False)
    answer_en: Mapped[str] = mapped_column(Text, nullable=False)
    answer_hi: Mapped[str] = mapped_column(Text, nullable=False)
    answer_mr: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus, name="faq_evidence_status"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class FaqCitation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "faq_citations"
    __table_args__ = (
        Index("ix_faq_citations_faq", "faq_id"),
        CheckConstraint("citation_order >= 0", name="faq_citation_order_non_negative"),
    )
    faq_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("faq_items.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_chunk_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("knowledge_chunks.id", ondelete="RESTRICT"), nullable=False
    )
    source_document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    citation_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ResponseCitation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "response_citations"
    __table_args__ = (Index("ix_response_citations_message", "message_id"),)
    message_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_chunk_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("knowledge_chunks.id", ondelete="RESTRICT"), nullable=False
    )
    citation_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MessageAttachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "message_attachments"
    __table_args__ = (
        CheckConstraint("file_size IS NULL OR file_size > 0", name="attachment_size_positive"),
        Index("ix_message_attachments_owner", "user_id", "chat_session_id"),
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    message_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="SET NULL")
    )
    chat_session_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    attachment_type: Mapped[AttachmentType] = mapped_column(
        Enum(AttachmentType, name="attachment_type"), nullable=False
    )
    source_type: Mapped[AttachmentSource] = mapped_column(
        Enum(AttachmentSource, name="attachment_source"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(1024))
    bucket_name: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(Integer)
    content_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    s3_etag: Mapped[str | None] = mapped_column(String(128))
    upload_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[AttachmentStatus] = mapped_column(
        Enum(AttachmentStatus, name="attachment_status"), nullable=False
    )


class GovernmentSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "government_sources"
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    organization: Mapped[str] = mapped_column(String(200), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(2048))
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trust_status: Mapped[TrustStatus] = mapped_column(
        Enum(TrustStatus, name="trust_status"), nullable=False
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class SourceDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_documents"
    __table_args__ = (Index("ix_source_documents_government_source_id", "government_source_id"),)
    government_source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("government_sources.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    canonical_url: Mapped[str | None] = mapped_column(String(2048), index=True)
    s3_key: Mapped[str | None] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(160))
    publication_date: Mapped[date | None] = mapped_column(Date)
    last_updated_date: Mapped[date | None] = mapped_column(Date)
    version: Mapped[str | None] = mapped_column(String(100))
    document_type: Mapped[str | None] = mapped_column(String(100))
    crop: Mapped[str | None] = mapped_column(String(80))
    region: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str | None] = mapped_column(String(16))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    page_count: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supersedes_document_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="source_document_status"), nullable=False
    )


class IngestionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_jobs"
    government_source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("government_sources.id", ondelete="RESTRICT"), nullable=False
    )
    source_document_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus, name="ingestion_status"), nullable=False
    )
    trigger_type: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType, name="ingestion_trigger_type"), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    chunks_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(String(1000))
    ingestion_version: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class KnowledgeChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        CheckConstraint("char_length(btrim(content)) > 0", name="content_non_empty"),
        CheckConstraint("embedding_dimension = 768", name="embedding_dimension_768"),
        CheckConstraint("chunk_index >= 0", name="chunk_index_non_negative"),
        Index("ix_knowledge_chunks_document", "source_document_id"),
        Index("ix_knowledge_chunks_filters", "crop", "topic", "language", "is_active"),
    )
    source_document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(160), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    crop: Mapped[str] = mapped_column(String(80), nullable=False)
    topic: Mapped[KnowledgeTopic] = mapped_column(
        Enum(KnowledgeTopic, name="knowledge_topic"), nullable=False
    )
    subtopic: Mapped[str | None] = mapped_column(String(160))
    crop_stage: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(500))
    source_reference: Mapped[str | None] = mapped_column(String(2048))
    publication_date: Mapped[date | None] = mapped_column(Date)
    ingestion_version: Mapped[str] = mapped_column(String(100), nullable=False)
    requires_regulatory_validation: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True)
    )


class ImageAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "image_analyses"
    __table_args__ = (
        Index("ix_image_analyses_user_id", "user_id"),
        Index("ix_image_analyses_idempotency", "content_hash", "model_name"),
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    crop_cycle_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("crop_cycles.id", ondelete="SET NULL")
    )
    attachment_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("message_attachments.id", ondelete="CASCADE"), unique=True
    )
    s3_key: Mapped[str | None] = mapped_column(String(1024))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="image_analysis_status"), nullable=False
    )
    observed_symptoms: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    possible_issue: Mapped[str | None] = mapped_column(Text)
    final_guidance: Mapped[str | None] = mapped_column(Text)
    quality_assessment: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    candidate_issues: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String(120))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Feedback(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="rating_range"),
        CheckConstraint(
            "message_id IS NOT NULL OR image_analysis_id IS NOT NULL "
            "OR faq_id IS NOT NULL OR comment IS NOT NULL",
            name="has_target_or_comment",
        ),
        Index("ix_feedback_user_id", "user_id"),
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    message_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="RESTRICT")
    )
    image_analysis_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("image_analyses.id", ondelete="RESTRICT")
    )
    faq_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("faq_items.id", ondelete="RESTRICT")
    )
    rating: Mapped[int | None] = mapped_column(Integer)
    is_helpful: Mapped[bool | None]
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
