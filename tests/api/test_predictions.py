from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from tests.agent.samples import GROUNDED
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
    sunday = await post(
        client,
        "/games",
        game(teams["DEN"], teams["LAC"], 1, "2026-09-13T13:00:00-04:00"),
    )
    await client.put(f"/games/{sunday}/score", json={"home": 20, "away": 20})
    rematch = await post(
        client, "/games", game(teams["LV"], teams["KC"], 2, "2026-09-20T16:25:00-04:00")
    )
    quarterback = await post(
        client, "/players", {"name": "Passer", "team_id": teams["LV"], "position": "QB"}
    )
    return teams | {"opener": opener, "rematch": rematch, "qb": quarterback}


async def test_predicts_game_with_both_sides(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.get(f"/games/{ids['rematch']}/prediction")

    assert response.status_code == 200
    prediction = response.json()
    assert prediction["home"]["team_id"] == ids["LV"]
    assert prediction["away"]["win_probability"] > 0.5
    assert prediction["home"]["win_probability"] + prediction["away"][
        "win_probability"
    ] == pytest.approx(1.0)
    assert prediction["home"]["rating"]["games_played"] == 1


async def test_absence_moves_the_prediction(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    healthy = (await client.get(f"/games/{ids['rematch']}/prediction")).json()

    reported = await client.put(
        f"/games/{ids['rematch']}/absences/{ids['qb']}", json={"status": "OUT"}
    )
    injured = (await client.get(f"/games/{ids['rematch']}/prediction")).json()

    assert reported.status_code == 200
    assert injured["home"]["win_probability"] < healthy["home"]["win_probability"]
    [impact] = injured["absences"]
    assert impact["player"]["id"] == ids["qb"]
    assert impact["affected_team_id"] == ids["LV"]
    assert impact["points_delta"] < 0


async def test_cleared_absence_restores_the_prediction(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    healthy = (await client.get(f"/games/{ids['rematch']}/prediction")).json()
    url = f"/games/{ids['rematch']}/absences/{ids['qb']}"
    await client.put(url, json={"status": "DOUBTFUL"})

    cleared = await client.delete(url)
    restored = (await client.get(f"/games/{ids['rematch']}/prediction")).json()

    assert cleared.status_code == 204
    assert (await client.get(f"/games/{ids['rematch']}/absences")).json() == []
    assert restored["spread"] == pytest.approx(healthy["spread"])


async def test_records_snapshot_history(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    recorded = await client.post(f"/games/{ids['rematch']}/prediction")
    history = await client.get(f"/games/{ids['rematch']}/prediction/history")

    assert recorded.status_code == 201
    [snapshot] = history.json()
    assert snapshot["home_win_probability"] == pytest.approx(
        recorded.json()["home"]["win_probability"]
    )


async def test_predicts_whole_week(client: AsyncClient, ids: dict[str, str]) -> None:
    response = await client.get("/predictions", params={"season": 2026, "week": 2})

    assert [p["game"]["id"] for p in response.json()] == [ids["rematch"]]


async def test_season_opener_has_insufficient_data(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.get(f"/games/{ids['opener']}/prediction")

    assert response.status_code == 409


async def test_preview_pairs_prediction_with_narrative(
    client: AsyncClient, ids: dict[str, str]
) -> None:
    response = await client.get(f"/games/{ids['rematch']}/preview")

    assert response.status_code == 200
    body = response.json()
    assert body["preview"]["headline"] == GROUNDED.headline
    assert body["prediction"]["game"]["id"] == ids["rematch"]


async def test_preview_unavailable_when_model_fails(
    app: FastAPI, client: AsyncClient, ids: dict[str, str]
) -> None:
    app.dependency_overrides[get_preview_writer] = FailingWriter

    response = await client.get(f"/games/{ids['rematch']}/preview")

    assert response.status_code == 503
