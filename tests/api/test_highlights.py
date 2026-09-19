import pytest
from httpx import AsyncClient

from tests.api.payloads import KANSAS_CITY


async def create(client: AsyncClient, url: str, payload: dict[str, object]) -> str:
    response = await client.post(url, json=payload)
    assert response.status_code == 201, response.text
    resource_id: str = response.json()["id"]
    return resource_id


@pytest.fixture
async def game_with_stats(client: AsyncClient) -> None:
    kc = await create(client, "/teams", KANSAS_CITY)
    lv = await create(client, "/teams", KANSAS_CITY | {"abbreviation": "LV"})
    game = await create(
        client,
        "/games",
        {
            "season": 2026,
            "week": 1,
            "kickoff": "2026-09-10T20:20:00-04:00",
            "home_team_id": kc,
            "away_team_id": lv,
        },
    )
    await client.put(f"/games/{game}/score", json={"home": 27, "away": 20})
    lines = {
        ("Passer", kc, "QB"): {"passing_yards": 275, "passing_touchdowns": 3},
        ("Runner", kc, "RB"): {"rushing_attempts": 21, "rushing_yards": 112},
        ("Scrambler", lv, "QB"): {"rushing_attempts": 5, "rushing_touchdowns": 1},
        ("Rusher", lv, "EDGE"): {"sacks": 2.5},
        ("Ballhawk", kc, "CB"): {"interceptions": 1},
    }
    for (name, team, position), numbers in lines.items():
        player = await create(
            client, "/players", {"name": name, "team_id": team, "position": position}
        )
        await client.put(f"/games/{game}/player-stats/{player}", json=numbers)


@pytest.mark.usefixtures("game_with_stats")
async def test_season_highlights(client: AsyncClient) -> None:
    response = await client.get("/highlights", params={"season": 2026})

    assert response.status_code == 200
    body = response.json()
    assert body["passing_yards"][0]["player"]["name"] == "Passer"
    assert body["passing_touchdowns"][0]["player"]["name"] == "Passer"
    assert body["rushing_touchdowns_qb"][0]["player"]["name"] == "Scrambler"
    assert body["yards_per_carry"][0]["yards_per_carry"] == pytest.approx(112 / 21)
    assert body["sacks"][0]["sacks"] == 2.5
    assert body["interceptions"][0]["player"]["name"] == "Ballhawk"


async def test_empty_season_has_no_leaders(client: AsyncClient) -> None:
    response = await client.get("/highlights", params={"season": 2030})

    assert response.json() == {
        "season": 2030,
        "passing_yards": [],
        "passing_touchdowns": [],
        "rushing_touchdowns_qb": [],
        "yards_per_carry": [],
        "sacks": [],
        "interceptions": [],
    }


async def test_limit_is_bounded(client: AsyncClient) -> None:
    response = await client.get("/highlights", params={"season": 2026, "limit": 0})

    assert response.status_code == 422
