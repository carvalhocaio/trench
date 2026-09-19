from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trench.domain.repositories import TeamRepository
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
