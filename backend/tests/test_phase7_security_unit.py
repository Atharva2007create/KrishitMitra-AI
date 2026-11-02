from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.routing import APIRoute

from app.api.v1.admin import _safe_metadata, router
from app.models.entities import User
from app.models.enums import UserRole
from app.security.cognito import CognitoClaims
from app.security.dependencies import get_current_user, require_admin


class ClaimsVerifier:
    def __init__(self, groups: frozenset[str]) -> None:
        self.groups = groups

    async def verify(self, _: str) -> CognitoClaims:
        return CognitoClaims(
            subject="existing-user",
            token_use="access",
            phone_number=None,
            email=None,
            groups=self.groups,
            authenticated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )


class RoleSession:
    def __init__(self, user: User) -> None:
        self.user = user
        self.original_role = user.role
        self.new: set[User] = set()
        self.commits = 0

    async def scalar(self, _: object) -> User:
        return self.user

    def is_modified(self, user: User) -> bool:
        return user.role != self.original_role

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _: User) -> None:
        return None


async def test_admin_role_is_enforced_server_side() -> None:
    farmer = User(cognito_sub="farmer", role=UserRole.FARMER)
    admin = User(cognito_sub="admin", role=UserRole.ADMIN)

    with pytest.raises(HTTPException) as denied:
        await require_admin(farmer)

    assert denied.value.status_code == 403
    assert await require_admin(admin) is admin


def test_every_admin_route_requires_server_admin_dependency() -> None:
    routes = [route for route in router.routes if isinstance(route, APIRoute)]

    assert routes
    for route in routes:
        assert any(dependency.call is require_admin for dependency in route.dependant.dependencies)


def test_admin_metadata_redacts_credentials_recursively() -> None:
    value = {
        "safe": "visible",
        "access_token": "do-not-return",
        "nested": {"api_key": "do-not-return", "status": "ok"},
    }

    assert _safe_metadata(value) == {
        "safe": "visible",
        "access_token": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]", "status": "ok"},
    }


@pytest.mark.parametrize(
    ("stored_role", "groups", "expected_role"),
    [
        (UserRole.ADMIN, frozenset(), UserRole.FARMER),
        (UserRole.FARMER, frozenset({"administrators"}), UserRole.ADMIN),
        (UserRole.ADMIN, frozenset({"unsupported-role"}), UserRole.FARMER),
    ],
)
async def test_database_role_tracks_current_verified_cognito_groups(
    stored_role: UserRole,
    groups: frozenset[str],
    expected_role: UserRole,
) -> None:
    user = User(
        cognito_sub="existing-user",
        role=stored_role,
        last_login_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    session = RoleSession(user)

    result = await get_current_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="token"),
        session,  # type: ignore[arg-type]
        ClaimsVerifier(groups),  # type: ignore[arg-type]
    )

    assert result.role == expected_role
    assert session.commits == int(stored_role != expected_role)
