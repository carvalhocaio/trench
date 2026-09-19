from dataclasses import dataclass
from uuid import uuid7

import pytest

from tests.analytics.samples import DEN, KC, LV
from tests.factories import make_game, make_player
from tests.fakes import FakeAbsenceRepository, FakeGameRepository, FakePlayerRepository
from trench.application.errors import GameNotFoundError, TeamNotInGameError
from trench.application.injuries import InjuryReportService
from trench.domain.entities import Absence
from trench.domain.enums import AbsenceStatus, Position

GAME = make_game(KC, LV)
RECEIVER = make_player(KC, Position.WR, "Receiver")
OUTSIDER = make_player(DEN, Position.CB, "Outsider")


@dataclass(frozen=True)
class Setup:
    service: InjuryReportService
    absences: FakeAbsenceRepository


@pytest.fixture
async def setup() -> Setup:
    games = FakeGameRepository()
    await games.save(GAME)
    players = FakePlayerRepository()
    for player in (RECEIVER, OUTSIDER):
        await players.save(player)
    absences = FakeAbsenceRepository()
    return Setup(
        service=InjuryReportService(games=games, players=players, absences=absences),
        absences=absences,
    )


async def test_report_updates_status_along_the_week(setup: Setup) -> None:
    await setup.service.report(GAME.id, RECEIVER.id, AbsenceStatus.QUESTIONABLE)
    await setup.service.report(GAME.id, RECEIVER.id, AbsenceStatus.OUT)

    assert await setup.service.list_game(GAME.id) == [
        Absence(game_id=GAME.id, player_id=RECEIVER.id, status=AbsenceStatus.OUT)
    ]


async def test_clear_removes_player_from_report(setup: Setup) -> None:
    await setup.service.report(GAME.id, RECEIVER.id, AbsenceStatus.DOUBTFUL)

    await setup.service.clear(GAME.id, RECEIVER.id)

    assert await setup.service.list_game(GAME.id) == []


async def test_clear_is_idempotent(setup: Setup) -> None:
    await setup.service.clear(GAME.id, RECEIVER.id)

    assert await setup.absences.list_by_game(GAME.id) == []


async def test_report_requires_player_from_the_game(setup: Setup) -> None:
    with pytest.raises(TeamNotInGameError):
        await setup.service.report(GAME.id, OUTSIDER.id, AbsenceStatus.OUT)


async def test_report_requires_known_game(setup: Setup) -> None:
    with pytest.raises(GameNotFoundError):
        await setup.service.report(uuid7(), RECEIVER.id, AbsenceStatus.OUT)
