from typing import Any
from uuid import uuid7

import pytest
from httpx import AsyncClient

from tests.api.payloads import KANSAS_CITY

KICKOFF = "2026-09-20T17:00:00+00:00"


async def create_team(client: AsyncClient, abbreviation: str) -> str:
    response = await client.post(
        "/teams", json=KANSAS_CITY | {"abbreviation": abbreviation}
    )
    team_id: str = response.json()["id"]
    return team_id


@pytest.fixture
async def teams(client: AsyncClient) -> dict[str, str]:
    return {code: await create_team(client, code) for code in ("KC", "LV", "DEN")}


def game_payload(home: str, away: str, week: int = 3) -> dict[str, Any]:
    return {
        "season": 2026,
        "week": week,
        "kickoff": KICKOFF,
        "home_team_id": home,
        "away_team_id": away,
    }


async def test_schedule_and_score_game(
    client: AsyncClient, teams: dict[str, str]
) -> None:
    created = await client.post("/games", json=game_payload(teams["KC"], teams["LV"]))
    assert created.status_code == 201
    game = created.json()
    assert game["status"] == "SCHEDULED"
    assert game["score"] is None

    scored = await client.put(
        f"/games/{game['id']}/score", json={"home": 27, "away": 20}
    )

    assert scored.status_code == 200
    assert scored.json()["status"] == "FINAL"
    assert scored.json()["score"] == {"home": 27, "away": 20}


async def test_list_games_by_week_and_team(
    client: AsyncClient, teams: dict[str, str]
) -> None:
    await client.post("/games", json=game_payload(teams["KC"], teams["LV"], week=3))
    await client.post("/games", json=game_payload(teams["DEN"], teams["KC"], week=4))

    week_three = await client.get("/games", params={"season": 2026, "week": 3})
    kc_games = await client.get(
        "/games", params={"season": 2026, "team_id": teams["KC"]}
    )

    assert [g["week"] for g in week_three.json()] == [3]
    assert [g["week"] for g in kc_games.json()] == [3, 4]


async def test_double_booking_conflicts(
    client: AsyncClient, teams: dict[str, str]
) -> None:
    await client.post("/games", json=game_payload(teams["KC"], teams["LV"]))

    response = await client.post("/games", json=game_payload(teams["DEN"], teams["KC"]))

    assert response.status_code == 409


async def test_unknown_team_is_not_found(
    client: AsyncClient, teams: dict[str, str]
) -> None:
    response = await client.post("/games", json=game_payload(teams["KC"], str(uuid7())))

    assert response.status_code == 404


async def test_same_team_on_both_sides_is_unprocessable(
    client: AsyncClient, teams: dict[str, str]
) -> None:
    response = await client.post("/games", json=game_payload(teams["KC"], teams["KC"]))

    assert response.status_code == 422


@pytest.mark.parametrize(
    "override",
    [{"kickoff": "2026-09-20T17:00:00"}, {"week": 19}, {"score": {"home": 1}}],
)
async def test_rejects_invalid_game_payload(
    client: AsyncClient, teams: dict[str, str], override: dict[str, Any]
) -> None:
    payload = game_payload(teams["KC"], teams["LV"]) | override

    response = await client.post("/games", json=payload)

    assert response.status_code == 422


async def test_rejects_negative_score(
    client: AsyncClient, teams: dict[str, str]
) -> None:
    created = await client.post("/games", json=game_payload(teams["KC"], teams["LV"]))

    response = await client.put(
        f"/games/{created.json()['id']}/score", json={"home": -3, "away": 7}
    )

    assert response.status_code == 422


async def test_unknown_game_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/games/{uuid7()}")

    assert response.status_code == 404
