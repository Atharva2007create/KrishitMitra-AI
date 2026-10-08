from collections.abc import AsyncIterator, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import SessionFactory, get_db
from app.main import app
from app.models.entities import (
    AuditLog,
    ChatSession,
    CropCycle,
    Farm,
    FarmerProfile,
    Feedback,
    GovernmentSource,
    ImageAnalysis,
    IngestionJob,
    KnowledgeChunk,
    Message,
    SourceDocument,
    User,
)
from app.models.enums import UserRole
from app.security.dependencies import get_current_user


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as value:
        for model in [
            Feedback,
            AuditLog,
            Message,
            ImageAnalysis,
            KnowledgeChunk,
            IngestionJob,
            SourceDocument,
            ChatSession,
            CropCycle,
            Farm,
            FarmerProfile,
            User,
            GovernmentSource,
        ]:
            await value.execute(delete(model))
        await value.commit()
        yield value


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value
    app.dependency_overrides.clear()


@pytest.fixture
async def users(session: AsyncSession) -> tuple[User, User, User]:
    values = (
        User(cognito_sub="farmer-a", role=UserRole.FARMER, phone_number="+910000000001"),
        User(cognito_sub="farmer-b", role=UserRole.FARMER, phone_number="+910000000002"),
        User(cognito_sub="admin", role=UserRole.ADMIN, email="admin@example.test"),
    )
    session.add_all(values)
    await session.commit()
    for value in values:
        await session.refresh(value)
    return values


@pytest.fixture
def authenticate() -> Callable[[User], None]:
    def use(user: User) -> None:
        async def override_current_user() -> User:
            return user

        app.dependency_overrides[get_current_user] = override_current_user

    return use
