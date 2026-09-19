from tests.factories import SEASON, make_game
from tests.repositories.conftest import AfcWest, Repositories
from trench.domain.entities import Game, Score


async def test_save_and_get_scheduled_game(repos: Repositories, game: Game) -> None:
    assert await repos.games.get(game.id) == game


async def test_save_persists_final_score(repos: Repositories, game: Game) -> None:
    await repos.games.save(game.finalize(Score(home=27, away=20), at=game.kickoff))

    stored = await repos.games.get(game.id)
    assert stored is not None
    assert stored.score == Score(home=27, away=20)


async def test_list_by_season_filters_week(
    repos: Repositories, afc_west: AfcWest
) -> None:
    week_one = make_game(afc_west.kc, afc_west.lv, week=1)
    week_two = make_game(afc_west.den, afc_west.kc, week=2)
    last_season = make_game(afc_west.kc, afc_west.lv, season=SEASON - 1)
    for game in (week_two, last_season, week_one):
        await repos.games.save(game)

    assert await repos.games.list_by_season(SEASON) == [week_one, week_two]
    assert await repos.games.list_by_season(SEASON, week=2) == [week_two]


async def test_list_by_team_includes_home_and_away(
    repos: Repositories, afc_west: AfcWest
) -> None:
    home = make_game(afc_west.kc, afc_west.lv, week=1)
    away = make_game(afc_west.den, afc_west.kc, week=2)
    unrelated = make_game(afc_west.lac, afc_west.lv, week=2)
    for game in (home, away, unrelated):
        await repos.games.save(game)

    assert await repos.games.list_by_team(afc_west.kc.id, SEASON) == [home, away]
