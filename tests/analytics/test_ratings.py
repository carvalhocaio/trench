from uuid import uuid7

import pytest

from tests.factories import make_game, make_team
from trench.analytics.errors import InsufficientDataError
from trench.analytics.ratings import compute_ratings
from trench.domain.entities import Game, Score, Team

K = 3.0

KC, LV, DEN, LAC = (make_team(code) for code in ("KC", "LV", "DEN", "LAC"))


def final(home: Team, away: Team, points: tuple[int, int], *, week: int) -> Game:
    home_points, away_points = points
    return make_game(home, away, week=week).finalize(
        Score(home=home_points, away=away_points)
    )


WEEK_ONE = [final(KC, LV, (30, 10), week=1), final(DEN, LAC, (20, 20), week=1)]


def test_league_average_counts_each_team_game() -> None:
    ratings = compute_ratings(WEEK_ONE, shrinkage_games=K)

    assert ratings.league_points_avg == pytest.approx(20.0)


def test_shrinks_single_game_towards_league_average() -> None:
    kc = compute_ratings(WEEK_ONE, shrinkage_games=K).rating_for(KC.id)

    assert kc.games_played == 1
    assert kc.points_for_avg == pytest.approx((30 + K * 20) / (1 + K))
    assert kc.points_against_avg == pytest.approx((10 + K * 20) / (1 + K))


def test_strengths_are_relative_to_league_average() -> None:
    ratings = compute_ratings(WEEK_ONE, shrinkage_games=K)
    kc, lv = ratings.rating_for(KC.id), ratings.rating_for(LV.id)

    assert kc.offense_strength > 1.0 > lv.offense_strength
    assert kc.defense_strength < 1.0 < lv.defense_strength
    assert ratings.rating_for(DEN.id).offense_strength == pytest.approx(1.0)


def test_evidence_outweighs_prior_as_season_goes_on() -> None:
    season = [
        final(KC, LV, (30, 10), week=week)
        if week % 2
        else final(LV, KC, (10, 30), week=week)
        for week in range(1, 17)
    ]

    kc = compute_ratings(season, shrinkage_games=K).rating_for(KC.id)

    assert kc.points_for_avg == pytest.approx((16 * 30 + K * 20) / (16 + K))
    assert kc.points_for_avg > 28.0


def test_unknown_team_gets_neutral_rating() -> None:
    rating = compute_ratings(WEEK_ONE, shrinkage_games=K).rating_for(uuid7())

    assert rating.games_played == 0
    assert rating.offense_strength == pytest.approx(1.0)
    assert rating.defense_strength == pytest.approx(1.0)


def test_ignores_scheduled_games() -> None:
    scheduled = make_game(KC, DEN, week=2)

    ratings = compute_ratings([*WEEK_ONE, scheduled], shrinkage_games=K)

    assert ratings.rating_for(KC.id).games_played == 1


def test_requires_final_games() -> None:
    with pytest.raises(InsufficientDataError):
        compute_ratings([make_game(KC, LV)], shrinkage_games=K)


def test_rejects_non_positive_shrinkage() -> None:
    with pytest.raises(ValueError, match="positive"):
        compute_ratings(WEEK_ONE, shrinkage_games=0)
