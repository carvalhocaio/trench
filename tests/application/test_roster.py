from uuid import uuid7

import pytest

from tests.analytics.samples import DEN, KC
from tests.factories import make_team
from tests.fakes import FakePlayerRepository, FakeTeamRepository
from trench.application.errors import PlayerNotFoundError, TeamNotFoundError
from trench.application.roster import RosterService
from trench.domain.enums import Position


@pytest.fixture
async def roster() -> RosterService:
    teams = FakeTeamRepository()
    for team in (KC, DEN):
        await teams.save(team)
    return RosterService(teams=teams, players=FakePlayerRepository())


async def test_registers_player_in_team(roster: RosterService) -> None:
    player = await roster.register(name="Passer", team_id=KC.id, position=Position.QB)

    assert await roster.list_team(KC.id) == [player]


async def test_update_moves_traded_player(roster: RosterService) -> None:
    player = await roster.register(name="Rusher", team_id=KC.id, position=Position.EDGE)

    traded = await roster.update(
        player.id, name="Rusher", team_id=DEN.id, position=Position.EDGE
    )

    assert traded.id == player.id
    assert await roster.list_team(KC.id) == []
    assert await roster.list_team(DEN.id) == [traded]


async def test_register_requires_known_team(roster: RosterService) -> None:
    with pytest.raises(TeamNotFoundError):
        await roster.register(
            name="Ghost", team_id=make_team("XX").id, position=Position.WR
        )


async def test_update_requires_known_player(roster: RosterService) -> None:
    with pytest.raises(PlayerNotFoundError):
        await roster.update(uuid7(), name="Ghost", team_id=KC.id, position=Position.WR)
