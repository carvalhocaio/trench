from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid7

import pytest

from tests.analytics.samples import DEN, KC, LV
from tests.factories import SEASON, make_game, make_player
from tests.fakes import (
    FakeGameRepository,
    FakePlayerGameStatsRepository,
    FakePlayerRepository,
    FakeTeamGameStatsRepository,
)
from trench.application.errors import (
    GameNotFoundError,
    PlayerNotFoundError,
    TeamNotInGameError,
)
from trench.application.stats import GameStatsService
from trench.domain.entities import Game, TeamGameStats
from trench.domain.enums import Position
from trench.domain.errors import GameNotStartedError

GAME = make_game(KC, LV)
RUNNER = make_player(KC, Position.RB, "Runner")
OUTSIDER = make_player(DEN, Position.QB, "Outsider")
AFTER_KICKOFF = GAME.kickoff + timedelta(hours=3)


@dataclass(frozen=True)
class Setup:
    service: GameStatsService
    team_stats: FakeTeamGameStatsRepository
    player_stats: FakePlayerGameStatsRepository


@pytest.fixture
async def setup() -> Setup:
    games = FakeGameRepository()
    await games.save(GAME)
    players = FakePlayerRepository()
    for player in (RUNNER, OUTSIDER):
        await players.save(player)
    team_stats = FakeTeamGameStatsRepository(games)
    player_stats = FakePlayerGameStatsRepository(games)
    return Setup(
        service=GameStatsService(
            games=games,
            players=players,
            team_stats=team_stats,
            player_stats=player_stats,
            clock=lambda: AFTER_KICKOFF,
        ),
        team_stats=team_stats,
        player_stats=player_stats,
    )


def team_stats(game: Game = GAME, team_id: UUID = KC.id) -> TeamGameStats:
    return TeamGameStats(
        game_id=game.id,
        team_id=team_id,
        offensive_plays=64,
        passing_yards=231,
        rushing_yards=142,
        turnovers=0,
        sacks=2,
    )


async def test_records_team_stats(setup: Setup) -> None:
    await setup.service.record_team_stats(team_stats())

    assert await setup.team_stats.list_by_season(SEASON) == [team_stats()]


async def test_team_stats_require_participant(setup: Setup) -> None:
    with pytest.raises(TeamNotInGameError):
        await setup.service.record_team_stats(team_stats(team_id=DEN.id))


async def test_team_stats_require_known_game(setup: Setup) -> None:
    with pytest.raises(GameNotFoundError):
        await setup.service.record_team_stats(team_stats(make_game(KC, DEN)))


async def test_team_stats_before_kickoff_is_rejected() -> None:
    service = await _service_before_kickoff()

    with pytest.raises(GameNotStartedError):
        await service.record_team_stats(team_stats())


async def test_player_stats_take_the_players_team(setup: Setup) -> None:
    stats = await setup.service.record_player_stats(
        game_id=GAME.id,
        player_id=RUNNER.id,
        passing_touchdowns=0,
        rushing_attempts=18,
        rushing_yards=97,
        sacks=0.0,
    )

    assert stats.team_id == KC.id
    assert await setup.player_stats.list_by_season(SEASON) == [stats]


async def test_player_stats_require_participant_team(setup: Setup) -> None:
    with pytest.raises(TeamNotInGameError):
        await setup.service.record_player_stats(
            game_id=GAME.id,
            player_id=OUTSIDER.id,
            passing_touchdowns=2,
            rushing_attempts=0,
            rushing_yards=0,
            sacks=0.0,
        )


async def test_player_stats_require_known_player(setup: Setup) -> None:
    with pytest.raises(PlayerNotFoundError):
        await setup.service.record_player_stats(
            game_id=GAME.id,
            player_id=uuid7(),
            passing_touchdowns=0,
            rushing_attempts=0,
            rushing_yards=0,
            sacks=0.0,
        )


async def test_player_stats_before_kickoff_is_rejected() -> None:
    service = await _service_before_kickoff()

    with pytest.raises(GameNotStartedError):
        await service.record_player_stats(
            game_id=GAME.id,
            player_id=RUNNER.id,
            passing_touchdowns=0,
            rushing_attempts=1,
            rushing_yards=1,
            sacks=0.0,
        )


async def _service_before_kickoff() -> GameStatsService:
    games = FakeGameRepository()
    await games.save(GAME)
    players = FakePlayerRepository()
    await players.save(RUNNER)
    return GameStatsService(
        games=games,
        players=players,
        team_stats=FakeTeamGameStatsRepository(games),
        player_stats=FakePlayerGameStatsRepository(games),
        clock=lambda: GAME.kickoff - timedelta(hours=1),
    )


async def test_lists_stats_of_a_game(setup: Setup) -> None:
    await setup.service.record_team_stats(team_stats())
    line = await setup.service.record_player_stats(
        game_id=GAME.id,
        player_id=RUNNER.id,
        passing_touchdowns=0,
        rushing_attempts=12,
        rushing_yards=61,
        sacks=0.0,
    )

    stats = await setup.service.of_game(GAME.id)

    assert stats.team_stats == [team_stats()]
    assert stats.player_stats == [line]


async def test_stats_of_unknown_game(setup: Setup) -> None:
    with pytest.raises(GameNotFoundError):
        await setup.service.of_game(uuid7())
