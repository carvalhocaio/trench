from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api.payloads import KANSAS_CITY
from trench.domain.entities import Score
from trench.infrastructure.repositories.games import SqlGameRepository


async def post(client: AsyncClient, url: str, payload: dict[str, Any]) -> str:
    response = await client.post(url, json=payload)
    assert response.status_code == 201, response.text
    resource_id: str = response.json()["id"]
    return resource_id


def game(home: str, away: str, week: int, kickoff: str) -> dict[str, Any]:
    return {
        "season": 2026,
        "week": week,
        "kickoff": kickoff,
        "home_team_id": home,
        "away_team_id": away,
    }


@pytest.fixture
async def ids(client: AsyncClient) -> dict[str, str]:
    teams = {
        code: await post(client, "/teams", KANSAS_CITY | {"abbreviation": code})
        for code in ("KC", "LV", "DEN", "LAC")
    }
    opener = await post(
        client, "/games", game(teams["KC"], teams["LV"], 1, "2026-09-10T20:20:00-04:00")
    )
    await client.put(f"/games/{opener}/score", json={"home": 30, "away": 10})
    versus_den = await post(
        client,
        "/games",
        game(teams["KC"], teams["DEN"], 2, "2026-09-17T13:00:00-04:00"),
    )
    await client.put(f"/games/{versus_den}/score", json={"home": 24, "away": 17})
    versus_lac = await post(
        client,
        "/games",
        game(teams["LV"], teams["LAC"], 2, "2026-09-17T16:25:00-04:00"),
    )
    await client.put(f"/games/{versus_lac}/score", json={"home": 10, "away": 24})
    return teams | {
        "opener": opener,
        "versus_den": versus_den,
        "versus_lac": versus_lac,
    }


async def test_empty_season_has_no_calibration_data(client: AsyncClient) -> None:
    response = await client.get("/calibration", params={"season": 2099})

    assert response.status_code == 200
    body = response.json()
    assert body["backtest"] is None
    assert body["live"] == []


async def test_backtest_evaluates_games_from_two_weeks(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.get("/calibration", params={"season": 2026})

    assert response.status_code == 200
    backtest = response.json()["backtest"]
    assert backtest["forecasts"] == 2
    assert 0.0 <= backtest["brier_score"] <= 1.0
    assert 0.0 <= backtest["favorite_accuracy"] <= 1.0


async def test_live_view_counts_only_the_last_snapshot_before_kickoff(
    client: AsyncClient, session: AsyncSession
) -> None:
    kc = await post(client, "/teams", KANSAS_CITY | {"abbreviation": "KC"})
    lv = await post(client, "/teams", KANSAS_CITY | {"abbreviation": "LV"})
    den = await post(client, "/teams", KANSAS_CITY | {"abbreviation": "DEN"})
    lac = await post(client, "/teams", KANSAS_CITY | {"abbreviation": "LAC"})
    quarterback = await post(
        client, "/players", {"name": "Passer", "team_id": lv, "position": "QB"}
    )
    history = await post(
        client, "/games", game(den, lac, 1, "2026-09-10T20:20:00-04:00")
    )
    await client.put(f"/games/{history}/score", json={"home": 24, "away": 17})
    # The kickoff must stay in the far future so both snapshots below count as
    # "before kickoff". The score is finalized straight through the
    # repository, at a time past that kickoff, since the API itself can only
    # finalize a game once its real kickoff has passed.
    matchup = await post(client, "/games", game(kc, lv, 2, "2099-09-10T20:20:00-04:00"))

    first = await client.post(f"/games/{matchup}/prediction")
    await client.put(f"/games/{matchup}/absences/{quarterback}", json={"status": "OUT"})
    second = await client.post(f"/games/{matchup}/prediction")

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert (
        first.json()["home"]["win_probability"]
        != second.json()["home"]["win_probability"]
    )

    games = SqlGameRepository(session)
    stored_game = await games.get(UUID(matchup))
    assert stored_game is not None
    finalized = stored_game.finalize(Score(home=27, away=20), at=stored_game.kickoff)
    await games.save(finalized)

    response = await client.get("/calibration", params={"season": 2026})

    [live] = response.json()["live"]
    report = live["report"]
    assert report["forecasts"] == 1
    expected_probability = second.json()["home"]["win_probability"]
    assert report["brier_score"] == pytest.approx((expected_probability - 1.0) ** 2)


async def test_shrinkage_override_changes_backtest_and_is_echoed_back(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    default = await client.get("/calibration", params={"season": 2026})
    overridden = await client.get(
        "/calibration", params={"season": 2026, "shrinkage_games": 50}
    )

    assert overridden.json()["parameters"]["shrinkage_games"] == 50
    assert default.json()["parameters"]["shrinkage_games"] != 50
    assert overridden.json()["backtest"]["brier_score"] != pytest.approx(
        default.json()["backtest"]["brier_score"]
    )


@pytest.mark.parametrize(
    "params",
    [
        {"season": 2026, "shrinkage_games": 0},
        {"season": 2026, "home_field_advantage": 11},
        {"season": 2026, "score_margin_stddev": -1},
    ],
)
async def test_invalid_parameters_are_rejected(
    client: AsyncClient, params: dict[str, Any]
) -> None:
    response = await client.get("/calibration", params=params)

    assert response.status_code == 422
