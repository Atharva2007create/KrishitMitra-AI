from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AreaUnit,
    CropCycleStatus,
    Language,
    RecordStatus,
    SenderType,
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
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


class SourceDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_documents"
    __table_args__ = (Index("ix_source_documents_government_source_id", "government_source_id"),)
    government_source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("government_sources.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    s3_key: Mapped[str | None] = mapped_column(String(1024))
    publication_date: Mapped[date | None] = mapped_column(Date)
    last_updated_date: Mapped[date | None] = mapped_column(Date)
    version: Mapped[str | None] = mapped_column(String(100))
    document_type: Mapped[str | None] = mapped_column(String(100))
    crop: Mapped[str | None] = mapped_column(String(80))
    region: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="source_document_status"), nullable=False
    )


class ImageAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "image_analyses"
    __table_args__ = (Index("ix_image_analyses_user_id", "user_id"),)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    crop_cycle_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("crop_cycles.id", ondelete="SET NULL")
    )
    s3_key: Mapped[str | None] = mapped_column(String(1024))
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="image_analysis_status"), nullable=False
    )
    observed_symptoms: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    possible_issue: Mapped[str | None] = mapped_column(Text)
    final_guidance: Mapped[str | None] = mapped_column(Text)


class Feedback(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="rating_range"),
        CheckConstraint(
            "message_id IS NOT NULL OR image_analysis_id IS NOT NULL OR comment IS NOT NULL",
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
