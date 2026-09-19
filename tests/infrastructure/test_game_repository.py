from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.infrastructure.factories import SEASON, make_game, make_team
from trench.domain.entities import Score, Team
from trench.infrastructure.repositories.games import SqlGameRepository
from trench.infrastructure.repositories.teams import SqlTeamRepository


@dataclass(frozen=True)
class AfcWest:
    kc: Team
    lv: Team
    den: Team
    lac: Team


@pytest.fixture
def repository(session: AsyncSession) -> SqlGameRepository:
    return SqlGameRepository(session)


@pytest.fixture
async def afc_west(session: AsyncSession) -> AfcWest:
    teams = SqlTeamRepository(session)
    afc_west = AfcWest(
        kc=make_team("KC"),
        lv=make_team("LV"),
        den=make_team("DEN"),
        lac=make_team("LAC"),
    )
    for team in (afc_west.kc, afc_west.lv, afc_west.den, afc_west.lac):
        await teams.save(team)
    return afc_west


async def test_save_and_get_scheduled_game(
    repository: SqlGameRepository, afc_west: AfcWest
) -> None:
    game = make_game(afc_west.kc, afc_west.lv)

    await repository.save(game)

    assert await repository.get(game.id) == game


async def test_save_persists_final_score(
    repository: SqlGameRepository, afc_west: AfcWest
) -> None:
    game = make_game(afc_west.kc, afc_west.lv)
    await repository.save(game)

    await repository.save(game.finalize(Score(home=27, away=20)))

    stored = await repository.get(game.id)
    assert stored is not None
    assert stored.score == Score(home=27, away=20)


async def test_list_by_season_filters_week(
    repository: SqlGameRepository, afc_west: AfcWest
) -> None:
    week_one = make_game(afc_west.kc, afc_west.lv, week=1)
    week_two = make_game(afc_west.den, afc_west.kc, week=2)
    for game in (week_two, week_one):
        await repository.save(game)

    assert await repository.list_by_season(SEASON) == [week_one, week_two]
    assert await repository.list_by_season(SEASON, week=2) == [week_two]


async def test_list_by_team_includes_home_and_away(
    repository: SqlGameRepository, afc_west: AfcWest
) -> None:
    home = make_game(afc_west.kc, afc_west.lv, week=1)
    away = make_game(afc_west.den, afc_west.kc, week=2)
    unrelated = make_game(afc_west.lac, afc_west.lv, week=2)
    for game in (home, away, unrelated):
        await repository.save(game)

    assert await repository.list_by_team(afc_west.kc.id, SEASON) == [home, away]
