import math
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import pairwise

from trench.analytics.errors import InsufficientDataError

PROBABILITY_FLOOR = 1e-6
FAVORITE_BINS = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)


@dataclass(frozen=True, slots=True)
class Forecast:
    home_win_probability: float
    home_won: bool

    @property
    def favorite_probability(self) -> float:
        return max(self.home_win_probability, 1.0 - self.home_win_probability)

    @property
    def favorite_won(self) -> bool:
        home_favored = self.home_win_probability >= 0.5
        return self.home_won == home_favored


@dataclass(frozen=True, slots=True, kw_only=True)
class ReliabilityBin:
    lower: float
    upper: float
    forecasts: int
    mean_probability: float
    observed_rate: float


@dataclass(frozen=True, slots=True, kw_only=True)
class CalibrationReport:
    forecasts: int
    brier_score: float
    log_loss: float
    favorite_accuracy: float
    reliability: tuple[ReliabilityBin, ...]


def evaluate(forecasts: Iterable[Forecast]) -> CalibrationReport:
    sample = list(forecasts)
    if not sample:
        raise InsufficientDataError("no settled forecasts to evaluate")

    return CalibrationReport(
        forecasts=len(sample),
        brier_score=_mean((f.home_win_probability - f.home_won) ** 2 for f in sample),
        log_loss=_mean(_log_loss(f) for f in sample),
        favorite_accuracy=_mean(float(f.favorite_won) for f in sample),
        reliability=_reliability(sample),
    )


def _log_loss(forecast: Forecast) -> float:
    probability = min(
        max(forecast.home_win_probability, PROBABILITY_FLOOR), 1 - PROBABILITY_FLOOR
    )
    outcome_probability = probability if forecast.home_won else 1 - probability
    return -math.log(outcome_probability)


def _reliability(sample: list[Forecast]) -> tuple[ReliabilityBin, ...]:
    bins = []
    for lower, upper in pairwise(FAVORITE_BINS):
        members = [f for f in sample if _within(f.favorite_probability, lower, upper)]
        if members:
            bins.append(
                ReliabilityBin(
                    lower=lower,
                    upper=upper,
                    forecasts=len(members),
                    mean_probability=_mean(f.favorite_probability for f in members),
                    observed_rate=_mean(float(f.favorite_won) for f in members),
                )
            )
    return tuple(bins)


def _within(probability: float, lower: float, upper: float) -> bool:
    if upper == FAVORITE_BINS[-1]:
        return lower <= probability <= upper
    return lower <= probability < upper


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items)
