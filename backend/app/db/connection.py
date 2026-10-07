from typing import cast

import asyncpg  # type: ignore[import-untyped]

from app.core.settings import get_settings


def _asyncpg_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def check_database() -> bool:
    connection: asyncpg.Connection | None = None
    try:
        connection = await asyncpg.connect(_asyncpg_url(get_settings().database_url), timeout=3)
        return cast(int, await connection.fetchval("SELECT 1")) == 1
    except (OSError, asyncpg.PostgresError):
        return False
    finally:
        if connection is not None:
            await connection.close()
