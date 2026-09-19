from uuid import uuid7

from httpx import AsyncClient

KANSAS_CITY = {
    "name": "Kansas City Chiefs",
    "abbreviation": "KC",
    "conference": "AFC",
    "division": "WEST",
}


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_and_fetch_team(client: AsyncClient) -> None:
    created = await client.post("/teams", json=KANSAS_CITY)

    assert created.status_code == 201
    team = created.json()
    assert team["abbreviation"] == "KC"

    fetched = await client.get(f"/teams/{team['id']}")
    assert fetched.json() == team


async def test_list_teams_by_abbreviation(client: AsyncClient) -> None:
    for abbreviation in ("LV", "DEN"):
        await client.post("/teams", json=KANSAS_CITY | {"abbreviation": abbreviation})

    response = await client.get("/teams")

    assert [team["abbreviation"] for team in response.json()] == ["DEN", "LV"]


async def test_duplicated_abbreviation_conflicts(client: AsyncClient) -> None:
    await client.post("/teams", json=KANSAS_CITY)

    response = await client.post("/teams", json=KANSAS_CITY)

    assert response.status_code == 409


async def test_rejects_invalid_payload(client: AsyncClient) -> None:
    response = await client.post(
        "/teams", json=KANSAS_CITY | {"abbreviation": "kc", "conference": "XFL"}
    )

    assert response.status_code == 422
    fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert fields == {"abbreviation", "conference"}


async def test_unknown_team_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/teams/{uuid7()}")

    assert response.status_code == 404
