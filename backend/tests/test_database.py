from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_migration_created_core_schema_and_pgvector(session: AsyncSession) -> None:
    tables = set(
        await session.scalars(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        )
    )
    assert {
        "users",
        "farmer_profiles",
        "farms",
        "crop_cycles",
        "chat_sessions",
        "messages",
        "government_sources",
        "source_documents",
        "image_analyses",
        "feedback",
        "audit_logs",
    } <= tables
    assert await session.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
