from uuid import uuid7

from tests.factories import make_team
from tests.repositories.conftest import AfcWest, Repositories


async def test_save_and_get(repos: Repositories) -> None:
    team = make_team("KC")

    await repos.teams.save(team)

    assert await repos.teams.get(team.id) == team


async def test_get_missing_returns_none(repos: Repositories) -> None:
    assert await repos.teams.get(uuid7()) is None


async def test_get_by_abbreviation(repos: Repositories, afc_west: AfcWest) -> None:
    assert await repos.teams.get_by_abbreviation("DEN") == afc_west.den
    assert await repos.teams.get_by_abbreviation("NE") is None


async def test_list_all_orders_by_abbreviation(
    repos: Repositories, afc_west: AfcWest
) -> None:
    teams = await repos.teams.list_all()

    assert [team.abbreviation for team in teams] == ["DEN", "KC", "LAC", "LV"]
