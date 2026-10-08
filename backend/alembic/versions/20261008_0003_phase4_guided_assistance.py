"""Add Phase 4 guided assistance, FAQ and attachment foundation."""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa

from alembic import op

revision: str = "20261008_0003"
down_revision: str | None = "20261007_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

session_origin = sa.Enum("CATEGORY", "FAQ", "DIRECT", "OTHER", name="session_origin")
evidence_status = sa.Enum(
    "SUFFICIENT",
    "PARTIAL",
    "INSUFFICIENT",
    "REQUIRES_LIVE_DATA",
    "REQUIRES_REGULATORY_VALIDATION",
    "REQUIRES_IMAGE_ANALYSIS",
    name="evidence_status",
)
faq_evidence_status = sa.Enum(
    "SUFFICIENT",
    "PARTIAL",
    "INSUFFICIENT",
    "REQUIRES_LIVE_DATA",
    "REQUIRES_REGULATORY_VALIDATION",
    "REQUIRES_IMAGE_ANALYSIS",
    name="faq_evidence_status",
)
message_language = sa.Enum("EN", "HI", "MR", name="message_language")
attachment_type = sa.Enum("IMAGE", "DOCUMENT", name="attachment_type")
attachment_source = sa.Enum("UPLOAD", "CAMERA", "DOCUMENT_PICKER", name="attachment_source")
attachment_status = sa.Enum(
    "PENDING_UPLOAD",
    "UPLOADED",
    "PENDING_ANALYSIS",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    name="attachment_status",
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


CATEGORIES = [
    (
        "00000000-0000-4000-8000-000000000401",
        "SOWING_AND_SEEDS",
        "sowing-seeds",
        "Sowing & Seed Treatment",
        "बुवाई और बीज उपचार",
        "पेरणी आणि बीजप्रक्रिया",
        "seed",
        ["SOWING", "SEED", "SEED_TREATMENT", "SPACING"],
    ),
    (
        "00000000-0000-4000-8000-000000000402",
        "SOIL_AND_LAND",
        "soil-land",
        "Soil & Land Preparation",
        "मिट्टी और भूमि तैयारी",
        "माती आणि जमीन तयारी",
        "soil",
        ["SOIL", "LAND_PREPARATION", "DRAINAGE"],
    ),
    (
        "00000000-0000-4000-8000-000000000403",
        "FERTILIZER_AND_NUTRIENTS",
        "fertilizers-nutrients",
        "Fertilizers & Nutrients",
        "उर्वरक और पोषक तत्व",
        "खते आणि पोषकद्रव्ये",
        "nutrients",
        ["FERTILIZER", "NUTRIENT_MANAGEMENT"],
    ),
    (
        "00000000-0000-4000-8000-000000000404",
        "IRRIGATION_AND_DRAINAGE",
        "irrigation-drainage",
        "Irrigation & Drainage",
        "सिंचाई और जल निकासी",
        "सिंचन आणि निचरा",
        "water",
        ["IRRIGATION", "DRAINAGE"],
    ),
    (
        "00000000-0000-4000-8000-000000000405",
        "PESTS",
        "pests",
        "Pests & Insects",
        "कीट और हानिकारक जीव",
        "कीड आणि किडी",
        "bug",
        ["PEST"],
    ),
    (
        "00000000-0000-4000-8000-000000000406",
        "DISEASES",
        "diseases",
        "Diseases",
        "रोग",
        "रोग",
        "disease",
        ["DISEASE"],
    ),
    (
        "00000000-0000-4000-8000-000000000407",
        "CROP_SYMPTOMS",
        "crop-symptoms",
        "Crop Symptoms & Plant Health",
        "फसल के लक्षण और पौध स्वास्थ्य",
        "पिकाची लक्षणे आणि वनस्पती आरोग्य",
        "symptoms",
        ["DISEASE", "NUTRIENT_MANAGEMENT", "IRRIGATION", "PEST"],
    ),
    (
        "00000000-0000-4000-8000-000000000408",
        "WEEDS",
        "weeds",
        "Weed Management",
        "खरपतवार प्रबंधन",
        "तण व्यवस्थापन",
        "weeds",
        ["WEED_MANAGEMENT"],
    ),
    (
        "00000000-0000-4000-8000-000000000409",
        "FLOWERING_AND_PODS",
        "flowering-pods",
        "Flowering & Pod Development",
        "फूल और फली विकास",
        "फुलोरा आणि शेंग विकास",
        "flower",
        ["FLOWERING", "POD_DEVELOPMENT", "CROP_STAGE"],
    ),
    (
        "00000000-0000-4000-8000-000000000410",
        "HARVESTING",
        "harvesting",
        "Harvesting & Maturity",
        "कटाई और परिपक्वता",
        "काढणी आणि परिपक्वता",
        "harvest",
        ["HARVEST", "CROP_STAGE"],
    ),
    (
        "00000000-0000-4000-8000-000000000411",
        "POST_HARVEST",
        "post-harvest",
        "Post-Harvest, Storage & Milling",
        "कटाई के बाद, भंडारण और दाल मिलिंग",
        "काढणीनंतर, साठवण आणि डाळ मिलिंग",
        "storage",
        ["POST_HARVEST", "STORAGE", "PROCESSING", "MILLING"],
    ),
    (
        "00000000-0000-4000-8000-000000000412",
        "WEATHER_RELATED",
        "weather-related",
        "Weather-Related Issues",
        "मौसम संबंधी समस्याएं",
        "हवामानाशी संबंधित समस्या",
        "weather",
        ["CLIMATE", "IRRIGATION"],
        True,
    ),
    (
        "00000000-0000-4000-8000-000000000413",
        "MARKET_AND_SELLING",
        "market-selling",
        "Market & Selling",
        "बाजार और बिक्री",
        "बाजार आणि विक्री",
        "market",
        [],
        True,
    ),
    (
        "00000000-0000-4000-8000-000000000414",
        "OTHER_TUR_PROBLEM",
        "other-tur-problem",
        "Other Tur Problem",
        "अन्य अरहर समस्या",
        "इतर तूर समस्या",
        "other",
        ["OTHER"],
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    # Enum columns added to existing tables do not receive create-table events.
    for enum_type in (session_origin, evidence_status, message_language):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "problem_categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(80), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name_en", sa.String(160), nullable=False),
        sa.Column("display_name_hi", sa.String(160), nullable=False),
        sa.Column("display_name_mr", sa.String(160), nullable=False),
        sa.Column("description_en", sa.String(500), nullable=False),
        sa.Column("description_hi", sa.String(500), nullable=False),
        sa.Column("description_mr", sa.String(500), nullable=False),
        sa.Column("icon_key", sa.String(80)),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("requires_live_data", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("metadata", sa.JSON()),
        *timestamps(),
    )
    op.create_index(
        "ix_problem_categories_active_order",
        "problem_categories",
        ["is_active", "display_order"],
    )
    categories = sa.table(
        "problem_categories",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("display_name_en", sa.String()),
        sa.column("display_name_hi", sa.String()),
        sa.column("display_name_mr", sa.String()),
        sa.column("description_en", sa.String()),
        sa.column("description_hi", sa.String()),
        sa.column("description_mr", sa.String()),
        sa.column("icon_key", sa.String()),
        sa.column("display_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
        sa.column("requires_live_data", sa.Boolean()),
        sa.column("metadata", sa.JSON()),
    )
    op.bulk_insert(
        categories,
        [
            {
                "id": UUID(item[0]),
                "code": item[1],
                "slug": item[2],
                "display_name_en": item[3],
                "display_name_hi": item[4],
                "display_name_mr": item[5],
                "description_en": f"Guidance for {item[3].lower()} in Tur/Pigeonpea.",
                "description_hi": f"अरहर में {item[4]} के लिए मार्गदर्शन।",
                "description_mr": f"तूर पिकातील {item[5]} यासाठी मार्गदर्शन.",
                "icon_key": item[6],
                "display_order": order,
                "is_active": True,
                "requires_live_data": bool(item[8]) if len(item) > 8 else False,
                "metadata": {"rag_topics": item[7]},
            }
            for order, item in enumerate(CATEGORIES, 1)
        ],
    )

    op.create_table(
        "faq_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "problem_category_id",
            sa.Uuid(),
            sa.ForeignKey("problem_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("canonical_question", sa.Text(), nullable=False),
        sa.Column("question_en", sa.Text(), nullable=False),
        sa.Column("question_hi", sa.Text(), nullable=False),
        sa.Column("question_mr", sa.Text(), nullable=False),
        sa.Column("answer_en", sa.Text(), nullable=False),
        sa.Column("answer_hi", sa.Text(), nullable=False),
        sa.Column("answer_mr", sa.Text(), nullable=False),
        sa.Column("evidence_status", faq_evidence_status, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON()),
        *timestamps(),
    )
    op.create_index(
        "ix_faq_items_category_active_order",
        "faq_items",
        ["problem_category_id", "is_active", "display_order"],
    )
    op.create_table(
        "faq_citations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "faq_id", sa.Uuid(), sa.ForeignKey("faq_items.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "knowledge_chunk_id",
            sa.Uuid(),
            sa.ForeignKey("knowledge_chunks.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("citation_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("citation_order >= 0", name="faq_citation_order_non_negative"),
    )
    op.create_index("ix_faq_citations_faq", "faq_citations", ["faq_id"])

    op.add_column("chat_sessions", sa.Column("problem_category_id", sa.Uuid()))
    op.add_column("chat_sessions", sa.Column("selected_faq_id", sa.Uuid()))
    op.add_column(
        "chat_sessions",
        sa.Column("origin_type", session_origin, server_default="DIRECT", nullable=False),
    )
    op.create_foreign_key(
        "fk_chat_sessions_problem_category",
        "chat_sessions",
        "problem_categories",
        ["problem_category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_chat_sessions_selected_faq",
        "chat_sessions",
        "faq_items",
        ["selected_faq_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("messages", sa.Column("language", message_language))
    op.add_column("messages", sa.Column("intent", sa.String(80)))
    op.add_column("messages", sa.Column("evidence_status", evidence_status))
    op.add_column("messages", sa.Column("metadata", sa.JSON()))
    op.create_table(
        "response_citations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "message_id",
            sa.Uuid(),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "knowledge_chunk_id",
            sa.Uuid(),
            sa.ForeignKey("knowledge_chunks.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("citation_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_response_citations_message", "response_citations", ["message_id"])
    op.create_table(
        "message_attachments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="SET NULL")),
        sa.Column(
            "chat_session_id",
            sa.Uuid(),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attachment_type", attachment_type, nullable=False),
        sa.Column("source_type", attachment_source, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("s3_key", sa.String(1024)),
        sa.Column("file_size", sa.Integer()),
        sa.Column("status", attachment_status, nullable=False),
        *timestamps(),
        sa.CheckConstraint("file_size IS NULL OR file_size > 0", name="attachment_size_positive"),
    )
    op.create_index(
        "ix_message_attachments_owner", "message_attachments", ["user_id", "chat_session_id"]
    )
    op.drop_constraint(
        op.f("ck_feedback_ck_feedback_has_target_or_comment"),
        "feedback",
        type_="check",
    )
    op.add_column("feedback", sa.Column("faq_id", sa.Uuid()))
    op.create_foreign_key(
        "fk_feedback_faq", "feedback", "faq_items", ["faq_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_check_constraint(
        op.f("ck_feedback_has_target_or_comment"),
        "feedback",
        "message_id IS NOT NULL OR image_analysis_id IS NOT NULL "
        "OR faq_id IS NOT NULL OR comment IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_feedback_has_target_or_comment"), "feedback", type_="check")
    op.drop_constraint("fk_feedback_faq", "feedback", type_="foreignkey")
    op.drop_column("feedback", "faq_id")
    op.create_check_constraint(
        op.f("ck_feedback_ck_feedback_has_target_or_comment"),
        "feedback",
        "message_id IS NOT NULL OR image_analysis_id IS NOT NULL OR comment IS NOT NULL",
    )
    op.drop_index("ix_message_attachments_owner", table_name="message_attachments")
    op.drop_table("message_attachments")
    op.drop_index("ix_response_citations_message", table_name="response_citations")
    op.drop_table("response_citations")
    for column in ("metadata", "evidence_status", "intent", "language"):
        op.drop_column("messages", column)
    op.drop_constraint("fk_chat_sessions_selected_faq", "chat_sessions", type_="foreignkey")
    op.drop_constraint("fk_chat_sessions_problem_category", "chat_sessions", type_="foreignkey")
    for column in ("origin_type", "selected_faq_id", "problem_category_id"):
        op.drop_column("chat_sessions", column)
    op.drop_index("ix_faq_citations_faq", table_name="faq_citations")
    op.drop_table("faq_citations")
    op.drop_index("ix_faq_items_category_active_order", table_name="faq_items")
    op.drop_table("faq_items")
    op.drop_index("ix_problem_categories_active_order", table_name="problem_categories")
    op.drop_table("problem_categories")
    bind = op.get_bind()
    for enum_type in (
        attachment_status,
        attachment_source,
        attachment_type,
        message_language,
        faq_evidence_status,
        evidence_status,
        session_origin,
    ):
        enum_type.drop(bind, checkfirst=True)
