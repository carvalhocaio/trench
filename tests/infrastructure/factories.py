from datetime import UTC, datetime, timedelta

from trench.domain.entities import Game, Team
from trench.domain.enums import Conference, Division

SEASON = 2026
SEASON_OPENER = datetime(2026, 9, 10, 20, 20, tzinfo=UTC)


def make_team(abbreviation: str) -> Team:
    return Team(
        name=f"Team {abbreviation}",
        abbreviation=abbreviation,
        conference=Conference.AFC,
        division=Division.WEST,
    )


def make_game(home: Team, away: Team, *, week: int = 1) -> Game:
    return Game(
        season=SEASON,
        week=week,
        kickoff=SEASON_OPENER + timedelta(weeks=week - 1),
        home_team_id=home.id,
        away_team_id=away.id,
    )
