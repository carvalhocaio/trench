from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from trench.domain.entities import Score
from trench.domain.enums import AbsenceStatus, Position

API_ROOT = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
SCOREBOARD_URL = f"{API_ROOT}/scoreboard"
INJURIES_URL = f"{API_ROOT}/injuries"

_ABBREVIATION_ALIASES = {"WSH": "WAS"}
_ESPN_SLUGS = {"WAS": "wsh"}

_POSITION_ALIASES = {
    "C": Position.OL,
    "G": Position.OL,
    "OT": Position.OL,
    "DT": Position.DL,
    "DE": Position.EDGE,
    "FB": Position.RB,
    "PK": Position.K,
}

_STATUS_ALIASES = {
    "Out": AbsenceStatus.OUT,
    "Injured Reserve": AbsenceStatus.OUT,
    "Doubtful": AbsenceStatus.DOUBTFUL,
    "Questionable": AbsenceStatus.QUESTIONABLE,
}

_FLOAT_FIELDS = {"sacks", "tackles_for_loss"}

_CATEGORY_FIELDS: dict[str, dict[str, str]] = {
    "passing": {
        "passingYards": "passing_yards",
        "passingTouchdowns": "passing_touchdowns",
        "interceptions": "interceptions_thrown",
    },
    "rushing": {
        "rushingAttempts": "rushing_attempts",
        "rushingYards": "rushing_yards",
        "rushingTouchdowns": "rushing_touchdowns",
    },
    "receiving": {
        "receptions": "receptions",
        "receivingYards": "receiving_yards",
        "receivingTouchdowns": "receiving_touchdowns",
        "receivingTargets": "receiving_targets",
    },
    "fumbles": {"fumbles": "fumbles", "fumblesLost": "fumbles_lost"},
    "defensive": {
        "totalTackles": "tackles",
        "sacks": "sacks",
        "tacklesForLoss": "tackles_for_loss",
        "passesDefended": "passes_defended",
        "defensiveTouchdowns": "defensive_touchdowns",
    },
    "interceptions": {"interceptions": "interceptions"},
    "kickReturns": {
        "kickReturns": "kick_returns",
        "kickReturnYards": "kick_return_yards",
        "kickReturnTouchdowns": "kick_return_touchdowns",
    },
    "puntReturns": {
        "puntReturns": "punt_returns",
        "puntReturnYards": "punt_return_yards",
        "puntReturnTouchdowns": "punt_return_touchdowns",
    },
    "punting": {"punts": "punts", "puntYards": "punt_yards"},
}

_CATEGORY_SPLIT_FIELDS: dict[str, dict[str, tuple[str, str]]] = {
    "passing": {
        "completions/passingAttempts": ("passing_completions", "passing_attempts")
    },
    "kicking": {
        "fieldGoalsMade/fieldGoalAttempts": (
            "field_goals_made",
            "field_goals_attempted",
        ),
        "extraPointsMade/extraPointAttempts": (
            "extra_points_made",
            "extra_points_attempted",
        ),
    },
}


@dataclass(frozen=True, slots=True, kw_only=True)
class EspnGame:
    espn_id: str
    kickoff: datetime
    home_abbreviation: str
    away_abbreviation: str
    score: Score | None


@dataclass(frozen=True, slots=True, kw_only=True)
class EspnRosterPlayer:
    name: str
    position: Position


@dataclass(frozen=True, slots=True, kw_only=True)
class EspnInjury:
    team_name: str
    player_name: str
    status: AbsenceStatus | None


@dataclass(frozen=True, slots=True, kw_only=True)
class EspnTeamBoxScore:
    abbreviation: str
    offensive_plays: int
    passing_yards: int
    rushing_yards: int
    turnovers: int
    sacks: int


@dataclass(frozen=True, slots=True, kw_only=True)
class EspnPlayerBoxScore:
    name: str
    team_abbreviation: str
    fields: dict[str, Any]


@dataclass(frozen=True, slots=True, kw_only=True)
class EspnBoxScore:
    teams: list[EspnTeamBoxScore]
    players: list[EspnPlayerBoxScore]


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
        espn_id=str(event["id"]),
        kickoff=kickoff,
        home_abbreviation=normalize_abbreviation(str(home["team"]["abbreviation"])),
        away_abbreviation=normalize_abbreviation(str(away["team"]["abbreviation"])),
        score=score,
    )


def normalize_abbreviation(abbreviation: str) -> str:
    return _ABBREVIATION_ALIASES.get(abbreviation, abbreviation)


def _espn_slug(abbreviation: str) -> str:
    return _ESPN_SLUGS.get(abbreviation, abbreviation).lower()


def _map_position(abbreviation: str) -> Position | None:
    if abbreviation in _POSITION_ALIASES:
        return _POSITION_ALIASES[abbreviation]
    try:
        return Position(abbreviation)
    except ValueError:
        return None


async def fetch_roster(
    client: httpx.AsyncClient, team_abbreviation: str
) -> list[EspnRosterPlayer]:
    response = await client.get(
        f"{API_ROOT}/teams/{_espn_slug(team_abbreviation)}/roster"
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    players = []
    for group in payload.get("athletes", []):
        for item in group.get("items", []):
            position = _map_position(item.get("position", {}).get("abbreviation", ""))
            if position is None:
                continue
            players.append(EspnRosterPlayer(name=item["fullName"], position=position))
    return players


async def fetch_injuries(client: httpx.AsyncClient) -> list[EspnInjury]:
    response = await client.get(INJURIES_URL)
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    injuries = []
    for team in payload.get("injuries", []):
        for injury in team.get("injuries", []):
            injuries.append(
                EspnInjury(
                    team_name=team["displayName"],
                    player_name=injury["athlete"]["displayName"],
                    status=_STATUS_ALIASES.get(injury.get("status", "")),
                )
            )
    return injuries


async def fetch_boxscore(client: httpx.AsyncClient, espn_id: str) -> EspnBoxScore:
    response = await client.get(f"{API_ROOT}/summary", params={"event": espn_id})
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    box = payload["boxscore"]
    teams = [_parse_team_box(team) for team in box.get("teams", [])]
    players = [
        player
        for team_players in box.get("players", [])
        for player in _parse_player_box(team_players)
    ]
    return EspnBoxScore(teams=teams, players=players)


def _stat_value(raw: str) -> int:
    try:
        return int(raw)
    except ValueError:
        return 0


def _float_stat_value(raw: str) -> float:
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _parse_team_box(team: dict[str, Any]) -> EspnTeamBoxScore:
    values = {s["name"]: s["displayValue"] for s in team["statistics"]}
    sacks = values.get("sacksYardsLost", "0-0").split("-")[0]
    return EspnTeamBoxScore(
        abbreviation=normalize_abbreviation(team["team"]["abbreviation"]),
        offensive_plays=_stat_value(values.get("totalOffensivePlays", "0")),
        passing_yards=_stat_value(values.get("netPassingYards", "0")),
        rushing_yards=_stat_value(values.get("rushingYards", "0")),
        turnovers=_stat_value(values.get("turnovers", "0")),
        sacks=_stat_value(sacks),
    )


def _parse_player_box(team_players: dict[str, Any]) -> list[EspnPlayerBoxScore]:
    abbreviation = normalize_abbreviation(team_players["team"]["abbreviation"])
    by_name: dict[str, dict[str, Any]] = {}
    for category in team_players.get("statistics", []):
        name = category.get("name", "")
        simple_fields = _CATEGORY_FIELDS.get(name, {})
        split_fields = _CATEGORY_SPLIT_FIELDS.get(name, {})
        if not simple_fields and not split_fields:
            continue
        keys = category.get("keys", [])
        for line in category.get("athletes", []):
            player_name = line["athlete"]["displayName"]
            fields = by_name.setdefault(player_name, {})
            for key, raw in zip(keys, line.get("stats", []), strict=False):
                _apply_stat(fields, key, raw, simple_fields, split_fields)
    return [
        EspnPlayerBoxScore(name=name, team_abbreviation=abbreviation, fields=fields)
        for name, fields in by_name.items()
    ]


def _apply_stat(
    fields: dict[str, Any],
    key: str,
    raw: str,
    simple_fields: dict[str, str],
    split_fields: dict[str, tuple[str, str]],
) -> None:
    if key in split_fields:
        made_field, attempted_field = split_fields[key]
        made, _, attempted = raw.partition("/")
        fields[made_field] = _stat_value(made)
        fields[attempted_field] = _stat_value(attempted)
    elif key in simple_fields:
        field_name = simple_fields[key]
        if field_name in _FLOAT_FIELDS:
            fields[field_name] = _float_stat_value(raw)
        else:
            fields[field_name] = _stat_value(raw)
