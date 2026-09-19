from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trench.application.schedule import ScheduleService
from trench.domain.repositories import GameRepository, TeamRepository
from trench.infrastructure.repositories.games import SqlGameRepository
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


def get_schedule_service(
    teams: TeamRepositoryDep, games: GameRepositoryDep
) -> ScheduleService:
    return ScheduleService(teams=teams, games=games)


ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]
