from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import FarmerProfile, User
from app.models.enums import Language

PROFILE = {
    "full_name": "Asha Patil",
    "preferred_language": "mr",
    "state": "Maharashtra",
    "district": "Pune",
    "taluka": "Baramati",
    "village": "Demo Village",
}
FARM = {
    "name": "North field",
    "area_value": "2.5",
    "area_unit": "ACRE",
    "state": "Maharashtra",
    "district": "Pune",
    "taluka": "Baramati",
}


async def test_missing_jwt_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 401


async def test_farmer_crud_and_admin_denial(
    client: AsyncClient,
    users: tuple[User, User, User],
    authenticate: Callable[[User], None],
) -> None:
    farmer, _, _ = users
    authenticate(farmer)
    assert (await client.get("/api/v1/me")).status_code == 200
    profile = await client.post("/api/v1/farmer/profile", json=PROFILE)
    assert profile.status_code == 201
    assert (
        await client.patch("/api/v1/farmer/profile", json={"village": "Updated"})
    ).status_code == 200

    farm = await client.post("/api/v1/farms", json=FARM)
    assert farm.status_code == 201
    farm_id = farm.json()["id"]
    assert len((await client.get("/api/v1/farms")).json()) == 1
    assert (
        await client.patch(f"/api/v1/farms/{farm_id}", json={"area_value": "3"})
    ).status_code == 200

    invalid_crop = await client.post(
        "/api/v1/crop-cycles",
        json={"farm_id": farm_id, "crop_name": "WHEAT", "sowing_date": "2026-06-01"},
    )
    assert invalid_crop.status_code == 422
    cycle = await client.post(
        "/api/v1/crop-cycles",
        json={"farm_id": farm_id, "crop_name": "Tur", "sowing_date": "2026-06-01"},
    )
    assert cycle.status_code == 201
    cycle_id = cycle.json()["id"]
    assert (
        await client.patch(f"/api/v1/crop-cycles/{cycle_id}", json={"status": "ACTIVE"})
    ).status_code == 200

    chat = await client.post(
        "/api/v1/chat/sessions", json={"crop_cycle_id": cycle_id, "language": "mr"}
    )
    assert chat.status_code == 201
    chat_id = chat.json()["id"]
    message = await client.post(
        f"/api/v1/chat/sessions/{chat_id}/messages", json={"content": "Test message"}
    )
    assert message.status_code == 201
    feedback = await client.post(
        "/api/v1/feedback", json={"message_id": message.json()["id"], "rating": 5}
    )
    assert feedback.status_code == 201
    assert (await client.get("/api/v1/admin/health")).status_code == 403
    assert (await client.delete(f"/api/v1/farms/{farm_id}")).status_code == 409


async def test_admin_access(
    client: AsyncClient,
    users: tuple[User, User, User],
    authenticate: Callable[[User], None],
) -> None:
    authenticate(users[2])
    response = await client.get("/api/v1/admin/health")
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


async def test_cross_user_isolation(
    client: AsyncClient,
    session: AsyncSession,
    users: tuple[User, User, User],
    authenticate: Callable[[User], None],
) -> None:
    farmer_a, farmer_b, _ = users
    profile_a = FarmerProfile(
        user_id=farmer_a.id,
        full_name="Farmer A",
        preferred_language=Language.EN,
        state="Maharashtra",
        district="Pune",
        taluka="Baramati",
    )
    profile_b = FarmerProfile(
        user_id=farmer_b.id,
        full_name="Farmer B",
        preferred_language=Language.HI,
        state="Maharashtra",
        district="Nashik",
        taluka="Niphad",
    )
    session.add_all([profile_a, profile_b])
    await session.commit()
    authenticate(farmer_b)
    farm = await client.post(
        "/api/v1/farms", json={**FARM, "district": "Nashik", "taluka": "Niphad"}
    )
    farm_id = farm.json()["id"]
    cycle = await client.post(
        "/api/v1/crop-cycles",
        json={"farm_id": farm_id, "crop_name": "Pigeonpea", "sowing_date": "2026-06-01"},
    )
    chat = await client.post("/api/v1/chat/sessions", json={"crop_cycle_id": cycle.json()["id"]})

    authenticate(farmer_a)
    assert (await client.get(f"/api/v1/farms/{farm_id}")).status_code == 404
    assert (
        await client.patch(f"/api/v1/farms/{farm_id}", json={"name": "stolen"})
    ).status_code == 404
    assert (await client.get(f"/api/v1/crop-cycles/{cycle.json()['id']}")).status_code == 404
    assert (await client.get(f"/api/v1/chat/sessions/{chat.json()['id']}")).status_code == 404
