from dataclasses import dataclass
from datetime import timedelta

import pytest

from tests.analytics.samples import DEN, KC, LAC, LV, WEEK_ONE, final
from tests.factories import make_game
from tests.fakes import (
    FakeAbsenceRepository,
    FakeGameRepository,
    FakePlayerRepository,
    FakePredictionSnapshotRepository,
    FakeTeamGameStatsRepository,
)
from trench.application.calibration import CalibrationService
from trench.application.predictions import PredictionService
from trench.config import AnalyticsSettings
from trench.domain.entities import Game, PredictionSnapshot

SEASON = 2026


@dataclass(frozen=True)
class Setup:
    games: FakeGameRepository
    snapshots: FakePredictionSnapshotRepository
    service: CalibrationService


@pytest.fixture
async def setup() -> Setup:
    games = FakeGameRepository()
    snapshots = FakePredictionSnapshotRepository(games)
    predictions = PredictionService(
        games=games,
        players=FakePlayerRepository(),
        absences=FakeAbsenceRepository(),
        snapshots=snapshots,
        team_stats=FakeTeamGameStatsRepository(games),
        settings=AnalyticsSettings(_env_file=None),  # pyright: ignore[reportCallIssue]
    )
    return Setup(
        games=games,
        snapshots=snapshots,
        service=CalibrationService(
            predictions=predictions, games=games, snapshots=snapshots
        ),
    )


async def save(setup: Setup, *games: Game) -> None:
    for game in games:
        await setup.games.save(game)


def snapshot(
    game: Game, *, probability: float, hours_before: float, version: str = "0.1.0"
) -> PredictionSnapshot:
    return PredictionSnapshot(
        game_id=game.id,
        as_of=game.kickoff - timedelta(hours=hours_before),
        home_projected_points=21.0,
        away_projected_points=20.0,
        home_win_probability=probability,
        model_version=version,
    )


async def test_backtest_skips_openers_ties_and_unplayed_games(setup: Setup) -> None:
    rematch = final(LV, KC, (13, 27), week=2)
    tie = final(LAC, DEN, (17, 17), week=2)
    await save(setup, *WEEK_ONE, rematch, tie, make_game(KC, DEN, week=3))

    report = await setup.service.backtest(SEASON)

    assert report is not None
    assert report.forecasts == 1
    assert report.favorite_accuracy == 1.0


async def test_backtest_without_settled_games_is_empty(setup: Setup) -> None:
    await save(setup, *WEEK_ONE)

    assert await setup.service.backtest(SEASON) is None


async def test_live_uses_last_snapshot_before_kickoff(setup: Setup) -> None:
    game = final(LV, KC, (13, 27), week=2)
    await save(setup, *WEEK_ONE, game)
    for item in (
        snapshot(game, probability=0.60, hours_before=96),
        snapshot(game, probability=0.20, hours_before=24),
        snapshot(game, probability=0.90, hours_before=-2),
    ):
        await setup.snapshots.save(item)

    report = (await setup.service.live(SEASON))["0.1.0"]

    assert report.forecasts == 1
    assert report.brier_score == pytest.approx(0.20**2)


async def test_live_reports_each_model_version(setup: Setup) -> None:
    game = final(LV, KC, (13, 27), week=2)
    await save(setup, *WEEK_ONE, game)
    await setup.snapshots.save(snapshot(game, probability=0.4, hours_before=24))
    await setup.snapshots.save(
        snapshot(game, probability=0.3, hours_before=24, version="0.2.0")
    )

    reports = await setup.service.live(SEASON)

    assert list(reports) == ["0.1.0", "0.2.0"]
    assert reports["0.2.0"].brier_score < reports["0.1.0"].brier_score


async def test_live_ignores_games_without_result(setup: Setup) -> None:
    upcoming = make_game(LV, KC, week=2)
    await save(setup, *WEEK_ONE, upcoming)
    await setup.snapshots.save(snapshot(upcoming, probability=0.4, hours_before=24))

    assert await setup.service.live(SEASON) == {}
