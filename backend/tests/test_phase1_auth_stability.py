from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.settings import Settings
from app.models.entities import User
from app.models.enums import UserRole
from app.security import dependencies
from app.security.cognito import CognitoClaims


class FakeVerifier:
    def __init__(self, claims: CognitoClaims) -> None:
        self.claims = claims

    async def verify(self, _: str) -> CognitoClaims:
        return self.claims


class FakeSession:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.new: set[User] = set()
        self.commit_count = 0
        self.refresh_count = 0

    async def scalar(self, _: object) -> User | None:
        return self.user

    def add(self, user: User) -> None:
        self.user = user
        self.new.add(user)

    def is_modified(self, _: User) -> bool:
        return False

    async def commit(self) -> None:
        self.commit_count += 1

    async def refresh(self, _: User) -> None:
        self.refresh_count += 1


def claims(authenticated_at: datetime) -> CognitoClaims:
    return CognitoClaims(
        subject="farmer-subject",
        token_use="access",
        phone_number=None,
        email=None,
        groups=frozenset(),
        authenticated_at=authenticated_at,
    )


async def test_reusing_session_does_not_write_last_login_on_every_request() -> None:
    authenticated_at = datetime(2026, 1, 1, tzinfo=UTC)
    user = User(
        cognito_sub="farmer-subject",
        role=UserRole.FARMER,
        last_login_at=authenticated_at,
    )
    session = FakeSession(user)

    result = await dependencies.get_current_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="token"),
        session,  # type: ignore[arg-type]
        FakeVerifier(claims(authenticated_at)),  # type: ignore[arg-type]
    )

    assert result is user
    assert session.commit_count == 0
    assert session.refresh_count == 0


async def test_inactive_user_is_rejected_without_database_mutation() -> None:
    authenticated_at = datetime(2026, 1, 1, tzinfo=UTC)
    user = User(
        cognito_sub="farmer-subject",
        role=UserRole.FARMER,
        is_active=False,
        last_login_at=authenticated_at,
    )
    session = FakeSession(user)

    with pytest.raises(HTTPException) as raised:
        await dependencies.get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="token"),
            session,  # type: ignore[arg-type]
            FakeVerifier(claims(authenticated_at)),  # type: ignore[arg-type]
        )

    assert raised.value.status_code == 403
    assert session.commit_count == 0


def test_jwt_verifier_is_reused_between_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        aws_cognito_user_pool_id="ap-south-1_test",
        aws_cognito_client_id="test-client",
    )
    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    dependencies.get_jwt_verifier.cache_clear()
    try:
        assert dependencies.get_jwt_verifier() is dependencies.get_jwt_verifier()
    finally:
        dependencies.get_jwt_verifier.cache_clear()
