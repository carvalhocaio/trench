import pytest

from tests.analytics.samples import DEN, KC, LAC, LV, WEEK_ONE, final
from tests.factories import make_game
from trench.analytics.home_field import compute_home_field_effect


def test_computes_home_win_rate_and_average_margin() -> None:
    effect = compute_home_field_effect(WEEK_ONE)

    assert effect.games == 2
    assert effect.home_win_rate == pytest.approx(1.0)
    assert effect.average_home_margin == pytest.approx((20 + 0) / 2)


def test_ignores_scheduled_games() -> None:
    scheduled = make_game(KC, DEN, week=2)

    effect = compute_home_field_effect([*WEEK_ONE, scheduled])

    assert effect.games == 2


def test_ties_count_towards_margin_but_not_win_rate() -> None:
    only_tie = [final(DEN, LAC, (20, 20), week=1)]

    effect = compute_home_field_effect(only_tie)

    assert effect.games == 1
    assert effect.home_win_rate is None
    assert effect.average_home_margin == pytest.approx(0.0)


def test_no_games_gives_no_effect() -> None:
    effect = compute_home_field_effect([])

    assert effect.games == 0
    assert effect.home_win_rate is None
    assert effect.average_home_margin is None


def test_away_wins_lower_the_home_win_rate() -> None:
    away_win = final(LV, KC, (10, 30), week=1)

    effect = compute_home_field_effect([away_win])

    assert effect.home_win_rate == pytest.approx(0.0)
    assert effect.average_home_margin == pytest.approx(-20.0)
