import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.api.v1.admin import _safe_metadata, router
from app.models.entities import User
from app.models.enums import UserRole
from app.security.dependencies import require_admin


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
