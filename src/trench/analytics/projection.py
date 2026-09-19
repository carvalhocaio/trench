from dataclasses import dataclass
from statistics import NormalDist
from uuid import UUID

from trench.analytics.absences import NO_ADJUSTMENT, PointsAdjustment
from trench.analytics.ratings import LeagueRatings


@dataclass(frozen=True, slots=True, kw_only=True)
class Projection:
    home_points: float
    away_points: float
    home_win_probability: float

    @property
    def spread(self) -> float:
        return self.home_points - self.away_points

    @property
    def away_win_probability(self) -> float:
        return 1.0 - self.home_win_probability


def project_game(
    ratings: LeagueRatings,
    *,
    home_team_id: UUID,
    away_team_id: UUID,
    home_field_advantage: float,
    score_margin_stddev: float,
    adjustment: PointsAdjustment = NO_ADJUSTMENT,
) -> Projection:
    if score_margin_stddev <= 0:
        raise ValueError("score_margin_stddev must be positive")

    home = ratings.rating_for(home_team_id)
    away = ratings.rating_for(away_team_id)
    home_edge = home_field_advantage / 2

    home_points = _expected_points(
        ratings.league_points_avg, home.offense_strength, away.defense_strength
    )
    away_points = _expected_points(
        ratings.league_points_avg, away.offense_strength, home.defense_strength
    )
    projected_home = max(0.0, home_points + home_edge + adjustment.home)
    projected_away = max(0.0, away_points - home_edge + adjustment.away)

    return Projection(
        home_points=projected_home,
        away_points=projected_away,
        home_win_probability=win_probability(
            projected_home - projected_away, score_margin_stddev
        ),
    )


def win_probability(spread: float, score_margin_stddev: float) -> float:
    return NormalDist(mu=0.0, sigma=score_margin_stddev).cdf(spread)


def _expected_points(
    league_points_avg: float, offense_strength: float, defense_strength: float
) -> float:
    return league_points_avg * offense_strength * defense_strength
