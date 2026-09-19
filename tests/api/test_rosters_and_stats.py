from typing import Any
from uuid import uuid7

import pytest
from httpx import AsyncClient

from tests.api.payloads import KANSAS_CITY

TEAM_STATS = {
    "offensive_plays": 64,
    "passing_yards": 231,
    "rushing_yards": 142,
    "turnovers": 1,
    "sacks": 3,
}


@pytest.fixture
async def ids(client: AsyncClient) -> dict[str, str]:
    teams = {}
    for code in ("KC", "LV", "DEN"):
        response = await client.post(
            "/teams", json=KANSAS_CITY | {"abbreviation": code}
        )
        teams[code] = response.json()["id"]
    game = await client.post(
        "/games",
        json={
            "season": 2026,
            "week": 3,
            "kickoff": "2026-09-10T17:00:00+00:00",
            "home_team_id": teams["KC"],
            "away_team_id": teams["LV"],
        },
    )
    runner = await register(client, "Runner", teams["KC"], "RB")
    return teams | {"game": game.json()["id"], "runner": runner["id"]}


async def register(
    client: AsyncClient, name: str, team_id: str, position: str
) -> dict[str, Any]:
    response = await client.post(
        "/players", json={"name": name, "team_id": team_id, "position": position}
    )
    assert response.status_code == 201
    player: dict[str, Any] = response.json()
    return player


@pytest.fixture
async def future_game(client: AsyncClient, ids: dict[str, str]) -> str:
    game = await client.post(
        "/games",
        json={
            "season": 2026,
            "week": 4,
            "kickoff": "2099-09-10T17:00:00+00:00",
            "home_team_id": ids["KC"],
            "away_team_id": ids["LV"],
        },
    )
    game_id: str = game.json()["id"]
    return game_id


async def test_roster_lists_and_trades_players(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    edge = await register(client, "Edge", ids["KC"], "EDGE")

    traded = await client.put(
        f"/players/{edge['id']}",
        json={"name": "Edge", "team_id": ids["DEN"], "position": "EDGE"},
    )
    kc_roster = await client.get(f"/teams/{ids['KC']}/players")

    assert traded.json()["team_id"] == ids["DEN"]
    assert [player["name"] for player in kc_roster.json()] == ["Runner"]


async def test_records_team_stats(client: AsyncClient, ids: dict[str, str]) -> None:
    response = await client.put(
        f"/games/{ids['game']}/team-stats/{ids['KC']}", json=TEAM_STATS
    )

    assert response.status_code == 200
    assert response.json()["total_yards"] == 373
    assert response.json()["yards_per_play"] == pytest.approx(373 / 64)


async def test_team_stats_for_team_outside_game(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.put(
        f"/games/{ids['game']}/team-stats/{ids['DEN']}", json=TEAM_STATS
    )

    assert response.status_code == 422


async def test_records_player_stats_with_players_team(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.put(
        f"/games/{ids['game']}/player-stats/{ids['runner']}",
        json={"rushing_attempts": 20, "rushing_yards": 94},
    )

    assert response.status_code == 200
    assert response.json()["team_id"] == ids["KC"]
    assert response.json()["yards_per_carry"] == pytest.approx(4.7)


async def test_records_receiving_and_defensive_stats(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.put(
        f"/games/{ids['game']}/player-stats/{ids['runner']}",
        json={
            "receptions": 4,
            "receiving_yards": 48,
            "receiving_touchdowns": 1,
            "tackles": 6,
            "tackles_for_loss": 1.5,
            "interceptions": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["yards_per_reception"] == pytest.approx(12.0)
    assert body["tackles"] == 6
    assert body["tackles_for_loss"] == 1.5
    assert body["interceptions"] == 1


@pytest.mark.parametrize("sacks", [0.3, -1.0])
async def test_rejects_invalid_sacks(
    client: AsyncClient, ids: dict[str, str], sacks: float
) -> None:
    response = await client.put(
        f"/games/{ids['game']}/player-stats/{ids['runner']}", json={"sacks": sacks}
    )

    assert response.status_code == 422


async def test_team_stats_before_kickoff_is_rejected(
    client: AsyncClient, ids: dict[str, str], future_game: str
) -> None:
    response = await client.put(
        f"/games/{future_game}/team-stats/{ids['KC']}", json=TEAM_STATS
    )

    assert response.status_code == 409
    assert response.json()["code"] == "game_not_started"


async def test_player_stats_before_kickoff_is_rejected(
    client: AsyncClient, ids: dict[str, str], future_game: str
) -> None:
    response = await client.put(
        f"/games/{future_game}/player-stats/{ids['runner']}",
        json={"rushing_attempts": 1},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "game_not_started"


async def test_player_stats_for_unknown_player(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.put(
        f"/games/{ids['game']}/player-stats/{uuid7()}", json={"rushing_attempts": 1}
    )

    assert response.status_code == 404


async def test_lists_recorded_stats_of_a_game(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    await client.put(f"/games/{ids['game']}/team-stats/{ids['KC']}", json=TEAM_STATS)
    await client.put(
        f"/games/{ids['game']}/player-stats/{ids['runner']}",
        json={"rushing_attempts": 20, "rushing_yards": 94},
    )

    response = await client.get(f"/games/{ids['game']}/stats")

    assert response.status_code == 200
    body = response.json()
    assert [row["team_id"] for row in body["team_stats"]] == [ids["KC"]]
    assert [row["player_id"] for row in body["player_stats"]] == [ids["runner"]]
