from tests.fakes import FakeTeamRepository
from trench.application.seed import seed_teams
from trench.domain.league import NFL_FRANCHISES


async def test_seeds_every_franchise() -> None:
    teams = FakeTeamRepository()

    result = await seed_teams(teams, NFL_FRANCHISES)

    assert len(result.created) == 32
    assert result.skipped == ()
    kc = await teams.get_by_abbreviation("KC")
    assert kc is not None
    assert kc.name == "Kansas City Chiefs"


async def test_seeding_twice_keeps_existing_teams() -> None:
    teams = FakeTeamRepository()
    await seed_teams(teams, NFL_FRANCHISES)
    first = await teams.list_all()

    result = await seed_teams(teams, NFL_FRANCHISES)

    assert result.created == ()
    assert len(result.skipped) == 32
    assert await teams.list_all() == first
