from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trench.application.roster import RosterService
from trench.application.schedule import ScheduleService
from trench.application.stats import GameStatsService
from trench.domain.repositories import (
    GameRepository,
    PlayerGameStatsRepository,
    PlayerRepository,
    TeamGameStatsRepository,
    TeamRepository,
)
from trench.infrastructure.repositories.games import SqlGameRepository
from trench.infrastructure.repositories.player_stats import (
    SqlPlayerGameStatsRepository,
)
from trench.infrastructure.repositories.players import SqlPlayerRepository
from trench.infrastructure.repositories.team_stats import SqlTeamGameStatsRepository
from trench.infrastructure.repositories.teams import SqlTeamRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.session_factory
    )
    async with session_factory() as session, session.begin():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_team_repository(session: SessionDep) -> TeamRepository:
    return SqlTeamRepository(session)


TeamRepositoryDep = Annotated[TeamRepository, Depends(get_team_repository)]


def get_game_repository(session: SessionDep) -> GameRepository:
    return SqlGameRepository(session)


GameRepositoryDep = Annotated[GameRepository, Depends(get_game_repository)]


def get_player_repository(session: SessionDep) -> PlayerRepository:
    return SqlPlayerRepository(session)


PlayerRepositoryDep = Annotated[PlayerRepository, Depends(get_player_repository)]


def get_team_stats_repository(session: SessionDep) -> TeamGameStatsRepository:
    return SqlTeamGameStatsRepository(session)


TeamStatsRepositoryDep = Annotated[
    TeamGameStatsRepository, Depends(get_team_stats_repository)
]


def get_player_stats_repository(session: SessionDep) -> PlayerGameStatsRepository:
    return SqlPlayerGameStatsRepository(session)


PlayerStatsRepositoryDep = Annotated[
    PlayerGameStatsRepository, Depends(get_player_stats_repository)
]


def get_schedule_service(
    teams: TeamRepositoryDep, games: GameRepositoryDep
) -> ScheduleService:
    return ScheduleService(teams=teams, games=games)


ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]


def get_roster_service(
    teams: TeamRepositoryDep, players: PlayerRepositoryDep
) -> RosterService:
    return RosterService(teams=teams, players=players)


RosterServiceDep = Annotated[RosterService, Depends(get_roster_service)]


def get_game_stats_service(
    games: GameRepositoryDep,
    players: PlayerRepositoryDep,
    team_stats: TeamStatsRepositoryDep,
    player_stats: PlayerStatsRepositoryDep,
) -> GameStatsService:
    return GameStatsService(
        games=games,
        players=players,
        team_stats=team_stats,
        player_stats=player_stats,
    )


GameStatsServiceDep = Annotated[GameStatsService, Depends(get_game_stats_service)]
