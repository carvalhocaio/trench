from uuid import uuid7

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.infrastructure.factories import make_team
from trench.infrastructure.repositories.teams import SqlTeamRepository


@pytest.fixture
def repository(session: AsyncSession) -> SqlTeamRepository:
    return SqlTeamRepository(session)


async def test_save_and_get(repository: SqlTeamRepository) -> None:
    team = make_team("KC")

    await repository.save(team)

    assert await repository.get(team.id) == team


async def test_get_missing_returns_none(repository: SqlTeamRepository) -> None:
    assert await repository.get(uuid7()) is None


async def test_get_by_abbreviation(repository: SqlTeamRepository) -> None:
    team = make_team("BUF")
    await repository.save(team)

    assert await repository.get_by_abbreviation("BUF") == team


async def test_list_all_orders_by_abbreviation(
    repository: SqlTeamRepository,
) -> None:
    for abbreviation in ("PHI", "DAL", "NYG"):
        await repository.save(make_team(abbreviation))

    teams = await repository.list_all()

    assert [team.abbreviation for team in teams] == ["DAL", "NYG", "PHI"]


async def test_rejects_duplicated_abbreviation(
    repository: SqlTeamRepository,
) -> None:
    await repository.save(make_team("KC"))

    with pytest.raises(IntegrityError):
        await repository.save(make_team("KC"))
