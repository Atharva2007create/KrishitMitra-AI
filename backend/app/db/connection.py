from collections.abc import AsyncIterator
from typing import cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.settings import get_settings

settings = get_settings()
if settings.app_env == "test":
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
else:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_database() -> bool:
    try:
        async with engine.connect() as connection:
            return cast(int, await connection.scalar(text("SELECT 1"))) == 1
    except (OSError, RuntimeError):
        return False
