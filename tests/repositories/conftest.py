from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_game, make_team
from tests.fakes import (
    FakeAbsenceRepository,
    FakeGameRepository,
    FakePlayerGameStatsRepository,
    FakePlayerRepository,
    FakePredictionSnapshotRepository,
    FakeTeamGameStatsRepository,
    FakeTeamRepository,
)
from trench.domain.entities import Game, Team
from trench.domain.repositories import (
    AbsenceRepository,
    GameRepository,
    PlayerGameStatsRepository,
    PlayerRepository,
    PredictionSnapshotRepository,
    TeamGameStatsRepository,
    TeamRepository,
)
from trench.infrastructure.repositories.absences import SqlAbsenceRepository
from trench.infrastructure.repositories.games import SqlGameRepository
from trench.infrastructure.repositories.player_stats import (
    SqlPlayerGameStatsRepository,
)
from trench.infrastructure.repositories.players import SqlPlayerRepository
from trench.infrastructure.repositories.predictions import (
    SqlPredictionSnapshotRepository,
)
from trench.infrastructure.repositories.team_stats import SqlTeamGameStatsRepository
from trench.infrastructure.repositories.teams import SqlTeamRepository


@dataclass(frozen=True)
class Repositories:
    teams: TeamRepository
    games: GameRepository
    players: PlayerRepository
    team_stats: TeamGameStatsRepository
    player_stats: PlayerGameStatsRepository
    absences: AbsenceRepository
    predictions: PredictionSnapshotRepository


@dataclass(frozen=True)
class AfcWest:
    kc: Team
    lv: Team
    den: Team
    lac: Team


def sql_repositories(session: AsyncSession) -> Repositories:
    return Repositories(
        teams=SqlTeamRepository(session),
        games=SqlGameRepository(session),
        players=SqlPlayerRepository(session),
        team_stats=SqlTeamGameStatsRepository(session),
        player_stats=SqlPlayerGameStatsRepository(session),
        absences=SqlAbsenceRepository(session),
        predictions=SqlPredictionSnapshotRepository(session),
    )


def fake_repositories() -> Repositories:
    games = FakeGameRepository()
    return Repositories(
        teams=FakeTeamRepository(),
        games=games,
        players=FakePlayerRepository(),
        team_stats=FakeTeamGameStatsRepository(games),
        player_stats=FakePlayerGameStatsRepository(games),
        absences=FakeAbsenceRepository(),
        predictions=FakePredictionSnapshotRepository(games),
    )


@pytest.fixture(params=["sql", "fake"])
def repos(request: pytest.FixtureRequest) -> Repositories:
    if request.param == "fake":
        return fake_repositories()
    return sql_repositories(request.getfixturevalue("session"))


@pytest.fixture
async def afc_west(repos: Repositories) -> AfcWest:
    afc_west = AfcWest(
        kc=make_team("KC"),
        lv=make_team("LV"),
        den=make_team("DEN"),
        lac=make_team("LAC"),
    )
    for team in (afc_west.kc, afc_west.lv, afc_west.den, afc_west.lac):
        await repos.teams.save(team)
    return afc_west


@pytest.fixture
async def game(repos: Repositories, afc_west: AfcWest) -> Game:
    game = make_game(afc_west.kc, afc_west.lv)
    await repos.games.save(game)
    return game
