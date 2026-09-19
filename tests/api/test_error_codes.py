from typing import Any
from uuid import uuid7

from fastapi import FastAPI
from httpx import AsyncClient

from tests.api.payloads import KANSAS_CITY
from trench.api.dependencies import get_preview_writer
from trench.application.previews import (
    MatchupContext,
    MatchupPreview,
    PreviewUnavailableError,
)


class FailingWriter:
    async def write(self, context: MatchupContext) -> MatchupPreview:
        raise PreviewUnavailableError("model timed out")


async def create_team(client: AsyncClient, abbreviation: str) -> str:
    response = await client.post(
        "/teams", json=KANSAS_CITY | {"abbreviation": abbreviation}
    )
    team_id: str = response.json()["id"]
    return team_id


def game(home: str, away: str, week: int, kickoff: str) -> dict[str, Any]:
    return {
        "season": 2026,
        "week": week,
        "kickoff": kickoff,
        "home_team_id": home,
        "away_team_id": away,
    }


async def test_not_found_has_its_code(client: AsyncClient) -> None:
    response = await client.get(f"/teams/{uuid7()}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_validation_error_has_its_code(client: AsyncClient) -> None:
    kc = await create_team(client, "KC")

    response = await client.post(
        "/games", json=game(kc, kc, 1, "2026-09-10T17:00:00+00:00")
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_team_not_in_game_has_its_code(client: AsyncClient) -> None:
    kc = await create_team(client, "KC")
    lv = await create_team(client, "LV")
    den = await create_team(client, "DEN")
    created = await client.post(
        "/games", json=game(kc, lv, 1, "2026-09-10T17:00:00+00:00")
    )

    response = await client.put(
        f"/games/{created.json()['id']}/team-stats/{den}",
        json={
            "offensive_plays": 1,
            "passing_yards": 1,
            "rushing_yards": 1,
            "turnovers": 0,
            "sacks": 0,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "team_not_in_game"


async def test_schedule_conflict_has_its_code(client: AsyncClient) -> None:
    kc = await create_team(client, "KC")
    lv = await create_team(client, "LV")
    den = await create_team(client, "DEN")
    await client.post("/games", json=game(kc, lv, 1, "2026-09-10T17:00:00+00:00"))

    response = await client.post(
        "/games", json=game(den, kc, 1, "2026-09-11T17:00:00+00:00")
    )

    assert response.status_code == 409
    assert response.json()["code"] == "schedule_conflict"


async def test_insufficient_data_has_its_code(client: AsyncClient) -> None:
    kc = await create_team(client, "KC")
    lv = await create_team(client, "LV")
    created = await client.post(
        "/games", json=game(kc, lv, 1, "2026-09-10T17:00:00+00:00")
    )

    response = await client.get(f"/games/{created.json()['id']}/prediction")

    assert response.status_code == 409
    assert response.json()["code"] == "insufficient_data"


async def test_game_not_started_has_its_code(client: AsyncClient) -> None:
    kc = await create_team(client, "KC")
    lv = await create_team(client, "LV")
    created = await client.post(
        "/games", json=game(kc, lv, 1, "2099-09-10T17:00:00+00:00")
    )

    response = await client.put(
        f"/games/{created.json()['id']}/score", json={"home": 1, "away": 0}
    )

    assert response.status_code == 409
    assert response.json()["code"] == "game_not_started"


async def test_preview_unavailable_has_its_code(
    app: FastAPI, client: AsyncClient
) -> None:
    app.dependency_overrides[get_preview_writer] = FailingWriter
    kc = await create_team(client, "KC")
    lv = await create_team(client, "LV")
    den = await create_team(client, "DEN")
    history = await client.post(
        "/games", json=game(kc, lv, 1, "2026-09-10T17:00:00+00:00")
    )
    await client.put(
        f"/games/{history.json()['id']}/score", json={"home": 24, "away": 17}
    )
    created = await client.post(
        "/games", json=game(den, kc, 2, "2026-09-17T17:00:00+00:00")
    )

    response = await client.get(f"/games/{created.json()['id']}/preview")

    assert response.status_code == 503
    assert response.json()["code"] == "preview_unavailable"


async def test_conflict_has_its_code(client: AsyncClient) -> None:
    await create_team(client, "KC")

    response = await client.post("/teams", json=KANSAS_CITY | {"abbreviation": "KC"})

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
