"""Add the Phase 3 government knowledge and retrieval schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "20261007_0002"
down_revision: str | None = "20261007_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ingestion_status = sa.Enum(
    "PENDING",
    "FETCHING",
    "PROCESSING",
    "EMBEDDING",
    "COMPLETED",
    "PARTIAL",
    "FAILED",
    name="ingestion_status",
)
trigger_type = sa.Enum("CLI", "RETRY", "REPROCESS", name="ingestion_trigger_type")
knowledge_topic = sa.Enum(
    "CROP_OVERVIEW",
    "CLIMATE",
    "SOIL",
    "LAND_PREPARATION",
    "VARIETY",
    "SEED",
    "SEED_TREATMENT",
    "SOWING",
    "SPACING",
    "INTERCROPPING",
    "NUTRIENT_MANAGEMENT",
    "FERTILIZER",
    "IRRIGATION",
    "DRAINAGE",
    "WEED_MANAGEMENT",
    "PEST",
    "DISEASE",
    "CROP_STAGE",
    "FLOWERING",
    "POD_DEVELOPMENT",
    "HARVEST",
    "POST_HARVEST",
    "STORAGE",
    "PROCESSING",
    "MILLING",
    "OTHER",
    name="knowledge_topic",
)


def upgrade() -> None:
    op.add_column("government_sources", sa.Column("last_verified_at", sa.DateTime(timezone=True)))
    op.add_column("government_sources", sa.Column("notes", sa.Text()))
    op.add_column("source_documents", sa.Column("canonical_url", sa.String(2048)))
    op.add_column("source_documents", sa.Column("mime_type", sa.String(160)))
    op.add_column("source_documents", sa.Column("language", sa.String(16)))
    op.add_column("source_documents", sa.Column("retrieved_at", sa.DateTime(timezone=True)))
    op.add_column("source_documents", sa.Column("content_hash", sa.String(64)))
    op.add_column("source_documents", sa.Column("page_count", sa.Integer()))
    op.add_column("source_documents", sa.Column("metadata", sa.JSON()))
    op.add_column(
        "source_documents",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column("source_documents", sa.Column("supersedes_document_id", sa.Uuid()))
    op.create_foreign_key(
        "fk_source_documents_supersedes_document_id_source_documents",
        "source_documents",
        "source_documents",
        ["supersedes_document_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_source_documents_content_hash", "source_documents", ["content_hash"])
    op.create_index("ix_source_documents_canonical_url", "source_documents", ["canonical_url"])

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "government_source_id",
            sa.Uuid(),
            sa.ForeignKey("government_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="SET NULL"),
        ),
        sa.Column("status", ingestion_status, nullable=False),
        sa.Column("trigger_type", trigger_type, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("chunks_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("chunks_failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_summary", sa.String(1000)),
        sa.Column("ingestion_version", sa.String(100), nullable=False),
        sa.Column("metadata", sa.JSON()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_ingestion_jobs_source", "ingestion_jobs", ["government_source_id"])
    op.create_index("ix_ingestion_jobs_document", "ingestion_jobs", ["source_document_id"])

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("embedding_model", sa.String(160), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("embedding_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("crop", sa.String(80), nullable=False),
        sa.Column("topic", knowledge_topic, nullable=False),
        sa.Column("subtopic", sa.String(160)),
        sa.Column("crop_stage", sa.String(120)),
        sa.Column("state", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("region", sa.String(120)),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("page_start", sa.Integer()),
        sa.Column("page_end", sa.Integer()),
        sa.Column("section_title", sa.String(500)),
        sa.Column("source_reference", sa.String(2048)),
        sa.Column("publication_date", sa.Date()),
        sa.Column("ingestion_version", sa.String(100), nullable=False),
        sa.Column(
            "requires_regulatory_validation",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("metadata", sa.JSON()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "search_vector",
            sa.dialects.postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', content)", persisted=True),
        ),
        sa.CheckConstraint("char_length(btrim(content)) > 0", name="content_non_empty"),
        sa.CheckConstraint("embedding_dimension = 768", name="embedding_dimension_768"),
        sa.CheckConstraint("chunk_index >= 0", name="chunk_index_non_negative"),
        sa.UniqueConstraint(
            "source_document_id",
            "ingestion_version",
            "chunk_index",
            name="uq_knowledge_chunk_version_index",
        ),
    )
    op.create_index("ix_knowledge_chunks_document", "knowledge_chunks", ["source_document_id"])
    op.create_index(
        "ix_knowledge_chunks_filters",
        "knowledge_chunks",
        ["crop", "topic", "language", "is_active"],
    )
    op.create_index("ix_knowledge_chunks_content_hash", "knowledge_chunks", ["content_hash"])
    op.create_index(
        "ix_knowledge_chunks_search_vector",
        "knowledge_chunks",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_knowledge_chunks_embedding_hnsw",
        "knowledge_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("ingestion_jobs")
    op.drop_index("ix_source_documents_canonical_url", table_name="source_documents")
    op.drop_index("ix_source_documents_content_hash", table_name="source_documents")
    op.drop_constraint(
        "fk_source_documents_supersedes_document_id_source_documents",
        "source_documents",
        type_="foreignkey",
    )
    for column in [
        "supersedes_document_id",
        "is_active",
        "metadata",
        "page_count",
        "content_hash",
        "retrieved_at",
        "language",
        "mime_type",
        "canonical_url",
    ]:
        op.drop_column("source_documents", column)
    op.drop_column("government_sources", "notes")
    op.drop_column("government_sources", "last_verified_at")
    knowledge_topic.drop(op.get_bind(), checkfirst=True)
    trigger_type.drop(op.get_bind(), checkfirst=True)
    ingestion_status.drop(op.get_bind(), checkfirst=True)
