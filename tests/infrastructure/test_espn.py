import httpx

from trench.domain.entities import Score
from trench.domain.enums import AbsenceStatus, Position
from trench.infrastructure.espn import (
    EspnTeamBoxScore,
    fetch_boxscore,
    fetch_injuries,
    fetch_roster,
    fetch_week,
)


def _event(
    *,
    espn_id: str = "401872932",
    date: str,
    completed: bool,
    home: str,
    away: str,
    home_score: int,
    away_score: int,
) -> dict[str, object]:
    return {
        "id": espn_id,
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
    assert game.espn_id == "401872932"
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


async def test_fetch_roster_maps_positions_and_skips_unmapped_ones() -> None:
    payload = {
        "athletes": [
            {
                "items": [
                    {"fullName": "Josh Allen", "position": {"abbreviation": "QB"}},
                    {"fullName": "Some Tackle", "position": {"abbreviation": "OT"}},
                    {"fullName": "A Defensive End", "position": {"abbreviation": "DE"}},
                    {"fullName": "A Kicker", "position": {"abbreviation": "PK"}},
                    {"fullName": "A Long Snapper", "position": {"abbreviation": "LS"}},
                ]
            }
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/teams/buf/roster")
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        roster = await fetch_roster(client, "BUF")

    by_name = {player.name: player.position for player in roster}
    assert by_name["Josh Allen"] == Position.QB
    assert by_name["Some Tackle"] == Position.OL
    assert by_name["A Defensive End"] == Position.EDGE
    assert by_name["A Kicker"] == Position.K
    assert "A Long Snapper" not in by_name


async def test_fetch_roster_uses_the_washington_slug() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/teams/wsh/roster")
        return httpx.Response(200, json={"athletes": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await fetch_roster(client, "WAS")


async def test_fetch_injuries_maps_statuses() -> None:
    payload = {
        "injuries": [
            {
                "displayName": "Arizona Cardinals",
                "injuries": [
                    {"status": "Questionable", "athlete": {"displayName": "Player A"}},
                    {"status": "Active", "athlete": {"displayName": "Player B"}},
                    {
                        "status": "Injured Reserve",
                        "athlete": {"displayName": "Player C"},
                    },
                ],
            }
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        injuries = await fetch_injuries(client)

    by_player = {injury.player_name: injury.status for injury in injuries}
    assert by_player["Player A"] == AbsenceStatus.QUESTIONABLE
    assert by_player["Player B"] is None
    assert by_player["Player C"] == AbsenceStatus.OUT


def _category(
    name: str, keys: list[str], athletes: list[dict[str, object]]
) -> dict[str, object]:
    return {"name": name, "keys": keys, "athletes": athletes}


async def test_fetch_boxscore_parses_team_and_player_stats() -> None:
    payload = {
        "boxscore": {
            "teams": [
                {
                    "team": {"abbreviation": "WSH"},
                    "statistics": [
                        {"name": "totalOffensivePlays", "displayValue": "60"},
                        {"name": "netPassingYards", "displayValue": "250"},
                        {"name": "rushingYards", "displayValue": "100"},
                        {"name": "turnovers", "displayValue": "1"},
                        {"name": "sacksYardsLost", "displayValue": "3-20"},
                    ],
                }
            ],
            "players": [
                {
                    "team": {"abbreviation": "WSH"},
                    "statistics": [
                        _category(
                            "passing",
                            ["completions/passingAttempts", "passingYards"],
                            [
                                {
                                    "athlete": {"displayName": "QB One"},
                                    "stats": ["20/30", "220"],
                                }
                            ],
                        ),
                        _category(
                            "receiving",
                            ["receptions", "receivingYards"],
                            [
                                {
                                    "athlete": {"displayName": "WR One"},
                                    "stats": ["5", "80"],
                                }
                            ],
                        ),
                        _category(
                            "kickReturns",
                            ["kickReturns", "kickReturnYards"],
                            [
                                {
                                    "athlete": {"displayName": "WR One"},
                                    "stats": ["2", "45"],
                                }
                            ],
                        ),
                    ],
                }
            ],
        }
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["event"] == "401872932"
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        box = await fetch_boxscore(client, "401872932")

    assert box.teams == [
        EspnTeamBoxScore(
            abbreviation="WAS",
            offensive_plays=60,
            passing_yards=250,
            rushing_yards=100,
            turnovers=1,
            sacks=3,
        )
    ]
    players = {player.name: player for player in box.players}
    assert players["QB One"].fields == {
        "passing_completions": 20,
        "passing_attempts": 30,
        "passing_yards": 220,
    }
    assert players["WR One"].fields == {
        "receptions": 5,
        "receiving_yards": 80,
        "kick_returns": 2,
        "kick_return_yards": 45,
    }
