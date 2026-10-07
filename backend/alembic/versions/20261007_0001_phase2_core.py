"""Create the Phase 2 core schema."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261007_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = sa.Enum("FARMER", "ADMIN", name="user_role")
language = sa.Enum("EN", "HI", "MR", name="language")
area_unit = sa.Enum("ACRE", "HECTARE", "GUNTHA", name="area_unit")
cycle_status = sa.Enum("PLANNED", "ACTIVE", "HARVESTED", "CANCELLED", name="crop_cycle_status")
chat_language = sa.Enum("EN", "HI", "MR", name="chat_language")
sender_type = sa.Enum("USER", "ASSISTANT", "SYSTEM", name="sender_type")
trust_status = sa.Enum("APPROVED", "PENDING", "DISABLED", name="trust_status")
document_status = sa.Enum(
    "PENDING", "PROCESSING", "COMPLETED", "FAILED", name="source_document_status"
)
analysis_status = sa.Enum(
    "PENDING", "PROCESSING", "COMPLETED", "FAILED", name="image_analysis_status"
)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cognito_sub", sa.String(128), nullable=False, unique=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("phone_number", sa.String(32), unique=True),
        sa.Column("email", sa.String(320), unique=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        *timestamps(),
    )
    op.create_table(
        "farmer_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("preferred_language", language, nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("taluka", sa.String(100), nullable=False),
        sa.Column("village", sa.String(120)),
        *timestamps(),
    )
    op.create_table(
        "farms",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "farmer_profile_id",
            sa.Uuid(),
            sa.ForeignKey("farmer_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120)),
        sa.Column("area_value", sa.Numeric(12, 3), nullable=False),
        sa.Column("area_unit", area_unit, nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("taluka", sa.String(100), nullable=False),
        sa.Column("village", sa.String(120)),
        sa.Column("soil_type", sa.String(100)),
        sa.Column("irrigation_type", sa.String(100)),
        sa.CheckConstraint("area_value > 0", name="ck_farms_area_positive"),
        *timestamps(),
    )
    op.create_index("ix_farms_farmer_profile_id", "farms", ["farmer_profile_id"])
    op.create_table(
        "crop_cycles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "farm_id", sa.Uuid(), sa.ForeignKey("farms.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("crop_name", sa.String(32), nullable=False),
        sa.Column("crop_variety", sa.String(120)),
        sa.Column("sowing_date", sa.Date(), nullable=False),
        sa.Column("expected_harvest_date", sa.Date()),
        sa.Column("actual_harvest_date", sa.Date()),
        sa.Column("status", cycle_status, nullable=False),
        sa.Column("estimated_crop_stage", sa.String(120)),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint(
            "crop_name IN ('TUR', 'PIGEONPEA')", name="ck_crop_cycles_supported_crop"
        ),
        sa.CheckConstraint(
            "expected_harvest_date IS NULL OR expected_harvest_date >= sowing_date",
            name="ck_crop_cycles_expected_harvest_after_sowing",
        ),
        sa.CheckConstraint(
            "actual_harvest_date IS NULL OR actual_harvest_date >= sowing_date",
            name="ck_crop_cycles_actual_harvest_after_sowing",
        ),
        *timestamps(),
    )
    op.create_index("ix_crop_cycles_farm_id", "crop_cycles", ["farm_id"])
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("crop_cycle_id", sa.Uuid(), sa.ForeignKey("crop_cycles.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(200)),
        sa.Column("language", chat_language, nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "chat_session_id",
            sa.Uuid(),
            sa.ForeignKey("chat_sessions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sender_type", sender_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_messages_chat_session_id", "messages", ["chat_session_id"])
    op.create_table(
        "government_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False, unique=True),
        sa.Column("organization", sa.String(200), nullable=False),
        sa.Column("base_url", sa.String(2048)),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("trust_status", trust_status, nullable=False),
        *timestamps(),
    )
    op.create_table(
        "source_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "government_source_id",
            sa.Uuid(),
            sa.ForeignKey("government_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("s3_key", sa.String(1024)),
        sa.Column("publication_date", sa.Date()),
        sa.Column("last_updated_date", sa.Date()),
        sa.Column("version", sa.String(100)),
        sa.Column("document_type", sa.String(100)),
        sa.Column("crop", sa.String(80)),
        sa.Column("region", sa.String(120)),
        sa.Column("status", document_status, nullable=False),
        *timestamps(),
    )
    op.create_index(
        "ix_source_documents_government_source_id", "source_documents", ["government_source_id"]
    )
    op.create_table(
        "image_analyses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("crop_cycle_id", sa.Uuid(), sa.ForeignKey("crop_cycles.id", ondelete="SET NULL")),
        sa.Column("s3_key", sa.String(1024)),
        sa.Column("status", analysis_status, nullable=False),
        sa.Column("observed_symptoms", sa.JSON()),
        sa.Column("possible_issue", sa.Text()),
        sa.Column("final_guidance", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_image_analyses_user_id", "image_analyses", ["user_id"])
    op.create_table(
        "feedback",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="RESTRICT")),
        sa.Column(
            "image_analysis_id", sa.Uuid(), sa.ForeignKey("image_analyses.id", ondelete="RESTRICT")
        ),
        sa.Column("rating", sa.Integer()),
        sa.Column("is_helpful", sa.Boolean()),
        sa.Column("comment", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_feedback_rating_range"
        ),
        sa.CheckConstraint(
            "message_id IS NOT NULL OR image_analysis_id IS NOT NULL OR comment IS NOT NULL",
            name="ck_feedback_has_target_or_comment",
        ),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(120), nullable=False),
        sa.Column("entity_id", sa.Uuid()),
        sa.Column("metadata", sa.JSON()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    for table in [
        "audit_logs",
        "feedback",
        "image_analyses",
        "source_documents",
        "government_sources",
        "messages",
        "chat_sessions",
        "crop_cycles",
        "farms",
        "farmer_profiles",
        "users",
    ]:
        op.drop_table(table)
    for enum_type in [
        analysis_status,
        document_status,
        trust_status,
        sender_type,
        chat_language,
        cycle_status,
        area_unit,
        language,
        user_role,
    ]:
        enum_type.drop(op.get_bind(), checkfirst=True)
