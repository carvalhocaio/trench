import math

import pytest

from trench.analytics.calibration import Forecast, evaluate
from trench.analytics.errors import InsufficientDataError


def test_perfect_forecasts_score_zero() -> None:
    report = evaluate([Forecast(1.0, True), Forecast(0.0, False)])

    assert report.brier_score == 0.0
    assert report.favorite_accuracy == 1.0
    assert report.log_loss == pytest.approx(0.0, abs=1e-5)


def test_coin_flips_score_a_quarter() -> None:
    report = evaluate([Forecast(0.5, True), Forecast(0.5, False)])

    assert report.brier_score == pytest.approx(0.25)
    assert report.log_loss == pytest.approx(math.log(2))


def test_confident_miss_is_punished_harder_by_log_loss() -> None:
    cautious = evaluate([Forecast(0.6, False)])
    confident = evaluate([Forecast(0.9, False)])

    assert confident.brier_score > cautious.brier_score
    assert confident.log_loss / cautious.log_loss > (
        confident.brier_score / cautious.brier_score
    )


def test_favorite_is_read_from_either_side() -> None:
    report = evaluate([Forecast(0.3, False), Forecast(0.7, False)])

    assert report.favorite_accuracy == 0.5


def test_reliability_groups_by_favorite_probability() -> None:
    forecasts = [
        Forecast(0.55, True),
        Forecast(0.45, True),
        Forecast(0.62, True),
        Forecast(0.35, False),
        Forecast(1.0, True),
    ]

    bins = {(b.lower, b.upper): b for b in evaluate(forecasts).reliability}

    assert set(bins) == {(0.5, 0.6), (0.6, 0.7), (0.9, 1.0)}
    coin_flips = bins[(0.5, 0.6)]
    assert coin_flips.forecasts == 2
    assert coin_flips.mean_probability == pytest.approx(0.55)
    assert coin_flips.observed_rate == pytest.approx(0.5)
    assert bins[(0.6, 0.7)].observed_rate == 1.0


def test_requires_forecasts() -> None:
    with pytest.raises(InsufficientDataError):
        evaluate([])
