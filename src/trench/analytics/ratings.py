from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from trench.analytics.errors import InsufficientDataError
from trench.domain.entities import Game
from trench.domain.enums import GameStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class TeamRating:
    team_id: UUID
    games_played: int
    points_for_avg: float
    points_against_avg: float
    offense_strength: float
    defense_strength: float


@dataclass(frozen=True, slots=True, kw_only=True)
class LeagueRatings:
    league_points_avg: float
    shrinkage_games: float
    teams: Mapping[UUID, TeamRating]

    def rating_for(self, team_id: UUID) -> TeamRating:
        return self.teams.get(team_id) or _rate(
            team_id,
            points_for=0,
            points_against=0,
            games_played=0,
            league_points_avg=self.league_points_avg,
            shrinkage_games=self.shrinkage_games,
        )


def compute_ratings(games: Iterable[Game], *, shrinkage_games: float) -> LeagueRatings:
    if shrinkage_games <= 0:
        raise ValueError("shrinkage_games must be positive")

    points_for: Counter[UUID] = Counter()
    points_against: Counter[UUID] = Counter()
    games_played: Counter[UUID] = Counter()
    for game in games:
        if game.status is not GameStatus.FINAL:
            continue
        for team_id in (game.home_team_id, game.away_team_id):
            points_for[team_id] += game.points_for(team_id)
            points_against[team_id] += game.points_against(team_id)
            games_played[team_id] += 1

    total_points = points_for.total()
    if total_points == 0:
        raise InsufficientDataError("no points scored in final games this season")

    league_points_avg = total_points / games_played.total()
    teams = {
        team_id: _rate(
            team_id,
            points_for=points_for[team_id],
            points_against=points_against[team_id],
            games_played=played,
            league_points_avg=league_points_avg,
            shrinkage_games=shrinkage_games,
        )
        for team_id, played in games_played.items()
    }
    return LeagueRatings(
        league_points_avg=league_points_avg,
        shrinkage_games=shrinkage_games,
        teams=teams,
    )


def _rate(
    team_id: UUID,
    *,
    points_for: int,
    points_against: int,
    games_played: int,
    league_points_avg: float,
    shrinkage_games: float,
) -> TeamRating:
    def shrink(total_points: int) -> float:
        prior_points = shrinkage_games * league_points_avg
        return (total_points + prior_points) / (games_played + shrinkage_games)

    points_for_avg = shrink(points_for)
    points_against_avg = shrink(points_against)
    return TeamRating(
        team_id=team_id,
        games_played=games_played,
        points_for_avg=points_for_avg,
        points_against_avg=points_against_avg,
        offense_strength=points_for_avg / league_points_avg,
        defense_strength=points_against_avg / league_points_avg,
    )
