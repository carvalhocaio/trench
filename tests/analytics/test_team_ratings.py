from uuid import uuid7

import pytest

from tests.analytics.samples import DEN, KC, LAC, LV, WEEK_ONE
from trench.analytics.absences import NO_ADJUSTMENT
from trench.analytics.errors import InsufficientDataError
from trench.analytics.team_ratings import (
    EfficiencyRating,
    LeagueEfficiencyRatings,
    assess_efficiency,
    compute_efficiency_ratings,
)
from trench.domain.entities import TeamGameStats

K = 3.0

KC_STATS = TeamGameStats(
    game_id=WEEK_ONE[0].id,
    team_id=KC.id,
    offensive_plays=60,
    passing_yards=200,
    rushing_yards=160,
    turnovers=0,
    sacks=1,
)
LV_STATS = TeamGameStats(
    game_id=WEEK_ONE[0].id,
    team_id=LV.id,
    offensive_plays=60,
    passing_yards=100,
    rushing_yards=80,
    turnovers=2,
    sacks=3,
)
DEN_STATS = TeamGameStats(
    game_id=WEEK_ONE[1].id,
    team_id=DEN.id,
    offensive_plays=60,
    passing_yards=120,
    rushing_yards=120,
    turnovers=1,
    sacks=2,
)
LAC_STATS = TeamGameStats(
    game_id=WEEK_ONE[1].id,
    team_id=LAC.id,
    offensive_plays=60,
    passing_yards=120,
    rushing_yards=120,
    turnovers=1,
    sacks=2,
)
STATS = [KC_STATS, LV_STATS, DEN_STATS, LAC_STATS]


def test_league_average_counts_each_team_game() -> None:
    ratings = compute_efficiency_ratings(WEEK_ONE, STATS, shrinkage_games=K)

    assert ratings.league_yards_per_play_avg == pytest.approx(4.25)


def test_shrinks_single_game_towards_league_average() -> None:
    kc = compute_efficiency_ratings(WEEK_ONE, STATS, shrinkage_games=K).rating_for(
        KC.id
    )

    assert kc.games_played == 1
    assert kc.yards_per_play_index == pytest.approx((6.0 + K * 4.25) / (1 + K) / 4.25)


def test_indices_are_relative_to_league_average() -> None:
    ratings = compute_efficiency_ratings(WEEK_ONE, STATS, shrinkage_games=K)
    kc, lv = ratings.rating_for(KC.id), ratings.rating_for(LV.id)

    assert kc.yards_per_play_index > 1.0 > lv.yards_per_play_index
    assert kc.yards_per_play_allowed_index < 1.0 < lv.yards_per_play_allowed_index
    assert kc.turnover_margin_index > 0.0 > lv.turnover_margin_index


def test_unknown_team_gets_neutral_rating() -> None:
    rating = compute_efficiency_ratings(WEEK_ONE, STATS, shrinkage_games=K).rating_for(
        uuid7()
    )

    assert rating.games_played == 0
    assert rating.yards_per_play_index == pytest.approx(1.0)
    assert rating.yards_per_play_allowed_index == pytest.approx(1.0)
    assert rating.turnover_margin_index == pytest.approx(0.0)


def test_rejects_non_positive_shrinkage() -> None:
    with pytest.raises(ValueError, match="positive"):
        compute_efficiency_ratings(WEEK_ONE, STATS, shrinkage_games=0)


def test_requires_some_team_stats() -> None:
    with pytest.raises(InsufficientDataError):
        compute_efficiency_ratings(WEEK_ONE, [], shrinkage_games=K)


def _ratings() -> LeagueEfficiencyRatings:
    return LeagueEfficiencyRatings(
        league_yards_per_play_avg=5.0,
        shrinkage_games=K,
        teams={
            KC.id: EfficiencyRating(
                team_id=KC.id,
                games_played=3,
                yards_per_play_index=1.2,
                yards_per_play_allowed_index=0.9,
                turnover_margin_index=0.3,
            ),
            LV.id: EfficiencyRating(
                team_id=LV.id,
                games_played=3,
                yards_per_play_index=0.9,
                yards_per_play_allowed_index=1.1,
                turnover_margin_index=-0.2,
            ),
        },
    )


def test_assess_efficiency_is_a_no_op_at_zero_weight() -> None:
    adjustment = assess_efficiency(WEEK_ONE[0], _ratings(), weight=0.0)

    assert adjustment is NO_ADJUSTMENT


def test_assess_efficiency_favors_the_more_efficient_side() -> None:
    adjustment = assess_efficiency(WEEK_ONE[0], _ratings(), weight=1.0)

    assert adjustment.home > 0.0
    assert adjustment.away == pytest.approx(-adjustment.home)


def test_assess_efficiency_scales_with_weight() -> None:
    small = assess_efficiency(WEEK_ONE[0], _ratings(), weight=1.0)
    large = assess_efficiency(WEEK_ONE[0], _ratings(), weight=2.0)

    assert large.home == pytest.approx(2 * small.home)
