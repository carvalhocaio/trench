from statistics import NormalDist
from uuid import uuid7

import pytest

from tests.analytics.samples import DEN, KC, LAC, LV, WEEK_ONE
from trench.analytics.projection import project_game, win_probability
from trench.analytics.ratings import compute_ratings

HFA = 1.7
SIGMA = 13.5
RATINGS = compute_ratings(WEEK_ONE, shrinkage_games=3.0)


def test_evenly_matched_teams_are_split_by_home_field_only() -> None:
    projection = project_game(
        RATINGS,
        home_team_id=DEN.id,
        away_team_id=LAC.id,
        home_field_advantage=HFA,
        score_margin_stddev=SIGMA,
    )

    assert projection.home_points == pytest.approx(20.0 + HFA / 2)
    assert projection.away_points == pytest.approx(20.0 - HFA / 2)
    assert projection.spread == pytest.approx(HFA)
    assert projection.home_win_probability == pytest.approx(
        NormalDist(0, SIGMA).cdf(HFA)
    )


def test_expected_points_combine_offense_and_opposing_defense() -> None:
    kc, lv = RATINGS.rating_for(KC.id), RATINGS.rating_for(LV.id)

    projection = project_game(
        RATINGS,
        home_team_id=KC.id,
        away_team_id=LV.id,
        home_field_advantage=0.0,
        score_margin_stddev=SIGMA,
    )

    league = RATINGS.league_points_avg
    assert projection.home_points == pytest.approx(
        league * kc.offense_strength * lv.defense_strength
    )
    assert projection.away_points == pytest.approx(
        league * lv.offense_strength * kc.defense_strength
    )
    assert projection.home_win_probability > 0.5


def test_swapping_sides_without_home_field_mirrors_probability() -> None:
    def kc_probability(home_is_kc: bool) -> float:
        projection = project_game(
            RATINGS,
            home_team_id=KC.id if home_is_kc else LV.id,
            away_team_id=LV.id if home_is_kc else KC.id,
            home_field_advantage=0.0,
            score_margin_stddev=SIGMA,
        )
        return (
            projection.home_win_probability
            if home_is_kc
            else projection.away_win_probability
        )

    assert kc_probability(home_is_kc=True) == pytest.approx(
        kc_probability(home_is_kc=False)
    )


def test_unknown_teams_get_coin_flip_without_home_field() -> None:
    projection = project_game(
        RATINGS,
        home_team_id=uuid7(),
        away_team_id=uuid7(),
        home_field_advantage=0.0,
        score_margin_stddev=SIGMA,
    )

    assert projection.home_win_probability == pytest.approx(0.5)


def test_projected_points_never_go_negative() -> None:
    projection = project_game(
        RATINGS,
        home_team_id=KC.id,
        away_team_id=LV.id,
        home_field_advantage=100.0,
        score_margin_stddev=SIGMA,
    )

    assert projection.away_points == 0.0


@pytest.mark.parametrize(
    ("spread", "expected"),
    [(0.0, 0.5), (SIGMA, NormalDist().cdf(1)), (-SIGMA, NormalDist().cdf(-1))],
)
def test_win_probability_follows_normal_margin(spread: float, expected: float) -> None:
    assert win_probability(spread, SIGMA) == pytest.approx(expected)


def test_wider_margin_spread_pulls_probability_towards_coin_flip() -> None:
    assert win_probability(7.0, 20.0) < win_probability(7.0, 10.0)


def test_rejects_non_positive_stddev() -> None:
    with pytest.raises(ValueError, match="positive"):
        project_game(
            RATINGS,
            home_team_id=KC.id,
            away_team_id=LV.id,
            home_field_advantage=HFA,
            score_margin_stddev=0.0,
        )
