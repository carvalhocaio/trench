import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_team
from trench.infrastructure.repositories.teams import SqlTeamRepository


async def test_rejects_duplicated_abbreviation(session: AsyncSession) -> None:
    repository = SqlTeamRepository(session)
    await repository.save(make_team("KC"))

    with pytest.raises(IntegrityError):
        await repository.save(make_team("KC"))
