from datetime import UTC, datetime, timedelta

from trench.domain.entities import Game, Player, Team
from trench.domain.enums import Conference, Division, Position

SEASON = 2026
SEASON_OPENER = datetime(2026, 9, 10, 20, 20, tzinfo=UTC)


def make_team(abbreviation: str) -> Team:
    return Team(
        name=f"Team {abbreviation}",
        abbreviation=abbreviation,
        conference=Conference.AFC,
        division=Division.WEST,
    )


def make_game(home: Team, away: Team, *, week: int = 1, season: int = SEASON) -> Game:
    return Game(
        season=season,
        week=week,
        kickoff=SEASON_OPENER.replace(year=season) + timedelta(weeks=week - 1),
        home_team_id=home.id,
        away_team_id=away.id,
    )


def make_player(team: Team, position: Position, name: str) -> Player:
    return Player(name=name, team_id=team.id, position=position)
