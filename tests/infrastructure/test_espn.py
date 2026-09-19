import httpx

from trench.domain.entities import Score
from trench.infrastructure.espn import fetch_week


def _event(
    *,
    date: str,
    completed: bool,
    home: str,
    away: str,
    home_score: int,
    away_score: int,
) -> dict[str, object]:
    return {
        "date": date,
        "competitions": [
            {
                "status": {"type": {"completed": completed}},
                "competitors": [
                    {
                        "homeAway": "home",
                        "team": {"abbreviation": home},
                        "score": str(home_score),
                    },
                    {
                        "homeAway": "away",
                        "team": {"abbreviation": away},
                        "score": str(away_score),
                    },
                ],
            }
        ],
    }


async def test_fetch_week_parses_a_completed_game() -> None:
    payload = {
        "events": [
            _event(
                date="2026-09-18T00:15Z",
                completed=True,
                home="BUF",
                away="DET",
                home_score=41,
                away_score=31,
            )
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["week"] == "2"
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        games = await fetch_week(client, 2026, 2)

    assert len(games) == 1
    game = games[0]
    assert game.kickoff.isoformat() == "2026-09-18T00:15:00+00:00"
    assert game.home_abbreviation == "BUF"
    assert game.away_abbreviation == "DET"
    assert game.score == Score(home=41, away=31)


async def test_fetch_week_leaves_scheduled_games_without_a_score() -> None:
    payload = {
        "events": [
            _event(
                date="2026-09-27T17:00Z",
                completed=False,
                home="WSH",
                away="DAL",
                home_score=0,
                away_score=0,
            )
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        games = await fetch_week(client, 2026, 3)

    assert games[0].score is None
    assert games[0].home_abbreviation == "WAS"
