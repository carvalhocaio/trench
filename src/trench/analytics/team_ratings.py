from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from trench.analytics.absences import NO_ADJUSTMENT, PointsAdjustment
from trench.analytics.efficiency import pair_with_opponent
from trench.analytics.errors import InsufficientDataError
from trench.domain.entities import Game, TeamGameStats


@dataclass(frozen=True, slots=True, kw_only=True)
class EfficiencyRating:
    team_id: UUID
    games_played: int
    yards_per_play_index: float
    yards_per_play_allowed_index: float
    turnover_margin_index: float


@dataclass(frozen=True, slots=True, kw_only=True)
class LeagueEfficiencyRatings:
    league_yards_per_play_avg: float
    shrinkage_games: float
    teams: Mapping[UUID, EfficiencyRating]

    def rating_for(self, team_id: UUID) -> EfficiencyRating:
        return self.teams.get(team_id) or EfficiencyRating(
            team_id=team_id,
            games_played=0,
            yards_per_play_index=1.0,
            yards_per_play_allowed_index=1.0,
            turnover_margin_index=0.0,
        )


def compute_efficiency_ratings(
    games: Iterable[Game], stats: Iterable[TeamGameStats], *, shrinkage_games: float
) -> LeagueEfficiencyRatings:
    """Bayesian-shrinkage ratings over yards/play and turnover margin.

    Mirrors analytics.ratings.compute_ratings: each team-game contributes one
    observation, shrunk toward the league average by shrinkage_games phantom
    games, exactly like points_for_avg/points_against_avg are shrunk there.
    """
    if shrinkage_games <= 0:
        raise ValueError("shrinkage_games must be positive")

    pairs = pair_with_opponent(games, stats)
    per_game_yards_per_play = [
        own.total_yards / own.offensive_plays
        for team_pairs in pairs.values()
        for own, _ in team_pairs
        if own.offensive_plays > 0
    ]
    if not per_game_yards_per_play:
        raise InsufficientDataError("no team stats available this season")
    league_yards_per_play_avg = sum(per_game_yards_per_play) / len(
        per_game_yards_per_play
    )

    teams = {
        team_id: _rate(
            team_id,
            team_pairs,
            league_yards_per_play_avg=league_yards_per_play_avg,
            shrinkage_games=shrinkage_games,
        )
        for team_id, team_pairs in pairs.items()
    }
    return LeagueEfficiencyRatings(
        league_yards_per_play_avg=league_yards_per_play_avg,
        shrinkage_games=shrinkage_games,
        teams=teams,
    )


def _rate(
    team_id: UUID,
    pairs: list[tuple[TeamGameStats, TeamGameStats]],
    *,
    league_yards_per_play_avg: float,
    shrinkage_games: float,
) -> EfficiencyRating:
    games_played = len(pairs)

    def shrink(total: float) -> float:
        prior = shrinkage_games * league_yards_per_play_avg
        return (total + prior) / (games_played + shrinkage_games)

    own_yards_per_play = sum(
        own.total_yards / own.offensive_plays
        for own, _ in pairs
        if own.offensive_plays > 0
    )
    opponent_yards_per_play = sum(
        opponent.total_yards / opponent.offensive_plays
        for _, opponent in pairs
        if opponent.offensive_plays > 0
    )
    turnover_margin = sum(opponent.turnovers - own.turnovers for own, opponent in pairs)

    return EfficiencyRating(
        team_id=team_id,
        games_played=games_played,
        yards_per_play_index=shrink(own_yards_per_play) / league_yards_per_play_avg,
        yards_per_play_allowed_index=shrink(opponent_yards_per_play)
        / league_yards_per_play_avg,
        turnover_margin_index=turnover_margin / (games_played + shrinkage_games),
    )


def assess_efficiency(
    game: Game, ratings: LeagueEfficiencyRatings, *, weight: float
) -> PointsAdjustment:
    """A small, symmetric point-spread shift from offense/defense efficiency
    and turnover margin, on top of the score-margin-based rating. weight=0.0
    (the default) makes this a strict no-op; a nonzero weight must be
    validated via GET /calibration before being trusted."""
    if weight == 0.0:
        return NO_ADJUSTMENT

    home = ratings.rating_for(game.home_team_id)
    away = ratings.rating_for(game.away_team_id)
    yardage_edge = (home.yards_per_play_index - away.yards_per_play_allowed_index) - (
        away.yards_per_play_index - home.yards_per_play_allowed_index
    )
    turnover_edge = home.turnover_margin_index - away.turnover_margin_index
    edge = weight * (yardage_edge + turnover_edge) / 2
    return PointsAdjustment(home=edge, away=-edge)
