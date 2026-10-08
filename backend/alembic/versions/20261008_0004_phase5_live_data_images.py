"""Add Phase 5 live data and image-analysis persistence fields."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261008_0004"
down_revision: str | None = "20261008_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE evidence_status ADD VALUE IF NOT EXISTS 'LIVE_DATA_UNAVAILABLE'")
    op.execute("ALTER TYPE faq_evidence_status ADD VALUE IF NOT EXISTS 'LIVE_DATA_UNAVAILABLE'")
    op.execute("ALTER TYPE image_analysis_status ADD VALUE IF NOT EXISTS 'IMAGE_INSUFFICIENT'")

    op.add_column("message_attachments", sa.Column("bucket_name", sa.String(255)))
    op.add_column("message_attachments", sa.Column("content_sha256", sa.String(64)))
    op.add_column("message_attachments", sa.Column("s3_etag", sa.String(128)))
    op.add_column(
        "message_attachments", sa.Column("upload_confirmed_at", sa.DateTime(timezone=True))
    )
    op.create_index(
        "ix_message_attachments_content_sha256", "message_attachments", ["content_sha256"]
    )

    op.add_column("image_analyses", sa.Column("attachment_id", sa.Uuid()))
    op.add_column("image_analyses", sa.Column("content_hash", sa.String(64)))
    op.add_column("image_analyses", sa.Column("model_name", sa.String(160)))
    op.add_column("image_analyses", sa.Column("quality_assessment", sa.JSON()))
    op.add_column("image_analyses", sa.Column("candidate_issues", sa.JSON()))
    op.add_column("image_analyses", sa.Column("evidence_json", sa.JSON()))
    op.add_column("image_analyses", sa.Column("error_code", sa.String(120)))
    op.add_column("image_analyses", sa.Column("processed_at", sa.DateTime(timezone=True)))
    op.create_foreign_key(
        "fk_image_analyses_attachment",
        "image_analyses",
        "message_attachments",
        ["attachment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_image_analyses_attachment_id", "image_analyses", ["attachment_id"]
    )
    op.create_index(
        "ix_image_analyses_idempotency",
        "image_analyses",
        ["content_hash", "model_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_image_analyses_idempotency", table_name="image_analyses")
    op.drop_constraint("uq_image_analyses_attachment_id", "image_analyses", type_="unique")
    op.drop_constraint("fk_image_analyses_attachment", "image_analyses", type_="foreignkey")
    for column in (
        "processed_at",
        "error_code",
        "evidence_json",
        "candidate_issues",
        "quality_assessment",
        "model_name",
        "content_hash",
        "attachment_id",
    ):
        op.drop_column("image_analyses", column)
    op.drop_index("ix_message_attachments_content_sha256", table_name="message_attachments")
    for column in ("upload_confirmed_at", "s3_etag", "content_sha256", "bucket_name"):
        op.drop_column("message_attachments", column)
    # PostgreSQL enum value removal is intentionally not attempted; it requires type recreation.
