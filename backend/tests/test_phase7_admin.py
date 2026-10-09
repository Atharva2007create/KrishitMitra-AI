from collections.abc import Callable

import pytest
from httpx import AsyncClient

from app.models.entities import User

ADMIN_ROUTES = [
    "/api/v1/admin/health",
    "/api/v1/admin/dashboard",
    "/api/v1/admin/users",
    "/api/v1/admin/sources",
    "/api/v1/admin/documents",
    "/api/v1/admin/ingestion",
    "/api/v1/admin/feedback",
    "/api/v1/admin/image-analyses",
    "/api/v1/admin/audit-logs",
    "/api/v1/admin/system",
]


@pytest.mark.parametrize("route", ADMIN_ROUTES)
async def test_farmer_cannot_access_admin_routes(
    route: str,
    client: AsyncClient,
    users: tuple[User, User, User],
    authenticate: Callable[[User], None],
) -> None:
    authenticate(users[0])

    response = await client.get(route)

    assert response.status_code == 403


async def test_admin_can_use_core_console_workflows(
    client: AsyncClient,
    users: tuple[User, User, User],
    authenticate: Callable[[User], None],
) -> None:
    farmer, _, admin = users
    authenticate(admin)

    for route in ADMIN_ROUTES:
        response = await client.get(route)
        assert response.status_code == 200, (route, response.text)

    detail = await client.get(f"/api/v1/admin/users/{farmer.id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["id"] == str(farmer.id)
    assert payload["role"] == "FARMER"
    assert "cognito_sub" not in payload
    assert "s3_key" not in detail.text
    assert "bucket_name" not in detail.text


async def test_admin_unknown_user_is_not_disclosed(
    client: AsyncClient,
    users: tuple[User, User, User],
    authenticate: Callable[[User], None],
) -> None:
    authenticate(users[2])

    response = await client.get("/api/v1/admin/users/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
