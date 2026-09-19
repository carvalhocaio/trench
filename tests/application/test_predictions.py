from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from uuid import uuid7

import pytest

from tests.analytics.samples import DEN, KC, LAC, LV, WEEK_ONE, final
from tests.factories import make_game, make_player
from tests.fakes import (
    FakeAbsenceRepository,
    FakeGameRepository,
    FakePlayerRepository,
    FakePredictionSnapshotRepository,
    FakeTeamGameStatsRepository,
)
from trench.analytics.errors import InsufficientDataError
from trench.application.errors import GameNotFoundError
from trench.application.predictions import MODEL_VERSION, PredictionService
from trench.config import AnalyticsSettings
from trench.domain.entities import Absence, Game, TeamGameStats
from trench.domain.enums import AbsenceStatus, Position

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
SETTINGS = AnalyticsSettings(_env_file=None)  # pyright: ignore[reportCallIssue]


@dataclass(frozen=True)
class World:
    games: FakeGameRepository
    players: FakePlayerRepository
    absences: FakeAbsenceRepository
    snapshots: FakePredictionSnapshotRepository
    team_stats: FakeTeamGameStatsRepository
    service: PredictionService


def _service(
    games: FakeGameRepository,
    players: FakePlayerRepository,
    absences: FakeAbsenceRepository,
    snapshots: FakePredictionSnapshotRepository,
    team_stats: FakeTeamGameStatsRepository,
    *,
    settings: AnalyticsSettings = SETTINGS,
) -> PredictionService:
    return PredictionService(
        games=games,
        players=players,
        absences=absences,
        snapshots=snapshots,
        team_stats=team_stats,
        settings=settings,
        clock=lambda: NOW,
    )


@pytest.fixture
async def world() -> World:
    games = FakeGameRepository()
    players = FakePlayerRepository()
    absences = FakeAbsenceRepository()
    snapshots = FakePredictionSnapshotRepository(games)
    team_stats = FakeTeamGameStatsRepository(games)
    for game in WEEK_ONE:
        await games.save(game)
    return World(
        games=games,
        players=players,
        absences=absences,
        snapshots=snapshots,
        team_stats=team_stats,
        service=_service(games, players, absences, snapshots, team_stats),
    )


async def schedule(world: World, game: Game) -> Game:
    await world.games.save(game)
    return game


async def test_predicts_from_games_played_before_kickoff(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))

    prediction = await world.service.predict(game.id)

    assert prediction.home_rating.games_played == 1
    assert prediction.projection.home_win_probability > 0.5
    assert prediction.as_of == NOW


async def test_ignores_results_after_kickoff(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))
    before = await world.service.predict(game.id)

    await world.games.save(final(LV, KC, (45, 0), week=3))
    after = await world.service.predict(game.id)

    assert after.projection == before.projection


async def test_applies_reported_absences(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))
    healthy = await world.service.predict(game.id)
    quarterback = make_player(KC, Position.QB, "Home Quarterback")
    await world.players.save(quarterback)

    await world.absences.save(
        Absence(game_id=game.id, player_id=quarterback.id, status=AbsenceStatus.OUT)
    )
    injured = await world.service.predict(game.id)

    assert injured.projection.home_points == pytest.approx(
        healthy.projection.home_points - SETTINGS.position_weights[Position.QB]
    )
    assert [impact.player for impact in injured.absences.impacts] == [quarterback]


async def test_predict_does_not_record_snapshot(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))

    await world.service.predict(game.id)

    assert await world.snapshots.list_by_game(game.id) == []


async def test_record_stores_snapshot(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))

    prediction = await world.service.record(game.id)

    [snapshot] = await world.snapshots.list_by_game(game.id)
    assert snapshot.as_of == NOW
    assert snapshot.model_version == MODEL_VERSION
    assert snapshot.home_win_probability == prediction.projection.home_win_probability


async def test_efficiency_weight_zero_is_a_no_op(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))
    baseline = await world.service.predict(game.id)

    await world.team_stats.save(
        TeamGameStats(
            game_id=WEEK_ONE[0].id,
            team_id=KC.id,
            offensive_plays=60,
            passing_yards=300,
            rushing_yards=200,
            turnovers=0,
            sacks=0,
        )
    )
    await world.team_stats.save(
        TeamGameStats(
            game_id=WEEK_ONE[0].id,
            team_id=LV.id,
            offensive_plays=60,
            passing_yards=50,
            rushing_yards=30,
            turnovers=3,
            sacks=5,
        )
    )

    still_baseline = await world.service.predict(game.id)

    assert still_baseline.projection == baseline.projection


async def test_nonzero_efficiency_weight_shifts_the_spread(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))
    await world.team_stats.save(
        TeamGameStats(
            game_id=WEEK_ONE[0].id,
            team_id=KC.id,
            offensive_plays=60,
            passing_yards=300,
            rushing_yards=200,
            turnovers=0,
            sacks=0,
        )
    )
    await world.team_stats.save(
        TeamGameStats(
            game_id=WEEK_ONE[0].id,
            team_id=LV.id,
            offensive_plays=60,
            passing_yards=50,
            rushing_yards=30,
            turnovers=3,
            sacks=5,
        )
    )
    baseline = await world.service.predict(game.id)

    boosted_settings = SETTINGS.model_copy(update={"efficiency_weight": 5.0})
    boosted_service = _service(
        world.games,
        world.players,
        world.absences,
        world.snapshots,
        world.team_stats,
        settings=boosted_settings,
    )
    boosted = await boosted_service.predict(game.id)

    assert boosted.projection.spread > baseline.projection.spread


async def test_predict_week_covers_every_game_of_the_week(world: World) -> None:
    sunday = await schedule(world, make_game(KC, LV, week=2))
    late = make_game(LAC, DEN, week=2)
    monday = await schedule(world, replace(late, kickoff=late.kickoff + timedelta(1)))

    predictions = await world.service.predict_week(2026, 2)

    assert [prediction.game for prediction in predictions] == [sunday, monday]


async def test_unknown_game_raises(world: World) -> None:
    with pytest.raises(GameNotFoundError):
        await world.service.predict(uuid7())


async def test_season_opener_has_no_data(world: World) -> None:
    opener = await schedule(world, make_game(DEN, KC, week=1, season=2027))

    with pytest.raises(InsufficientDataError):
        await world.service.predict(opener.id)


async def test_history_lists_recorded_snapshots(world: World) -> None:
    game = await schedule(world, make_game(KC, LV, week=2))
    await world.service.record(game.id)

    [snapshot] = await world.service.history(game.id)

    assert snapshot.game_id == game.id


async def test_history_of_unknown_game_raises(world: World) -> None:
    with pytest.raises(GameNotFoundError):
        await world.service.history(uuid7())
