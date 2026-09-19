from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from trench.domain.entities import Score

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

_ABBREVIATION_ALIASES = {"WSH": "WAS"}


@dataclass(frozen=True, slots=True, kw_only=True)
class EspnGame:
    kickoff: datetime
    home_abbreviation: str
    away_abbreviation: str
    score: Score | None


async def fetch_week(
    client: httpx.AsyncClient, season: int, week: int
) -> list[EspnGame]:
    response = await client.get(
        SCOREBOARD_URL, params={"seasontype": 2, "week": week, "dates": season}
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    return [_parse_event(event) for event in payload.get("events", [])]


def _parse_event(event: dict[str, Any]) -> EspnGame:
    competition = event["competitions"][0]
    completed = bool(competition["status"]["type"]["completed"])
    competitors = {c["homeAway"]: c for c in competition["competitors"]}
    home, away = competitors["home"], competitors["away"]
    score = (
        Score(home=int(home["score"]), away=int(away["score"])) if completed else None
    )
    kickoff = datetime.fromisoformat(str(event["date"]).replace("Z", "+00:00"))
    return EspnGame(
        kickoff=kickoff,
        home_abbreviation=_normalize(str(home["team"]["abbreviation"])),
        away_abbreviation=_normalize(str(away["team"]["abbreviation"])),
        score=score,
    )


def _normalize(abbreviation: str) -> str:
    return _ABBREVIATION_ALIASES.get(abbreviation, abbreviation)
