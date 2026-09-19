from tests.factories import SEASON, make_game, make_player
from tests.repositories.conftest import AfcWest, Repositories
from trench.domain.entities import Game, PlayerGameStats, TeamGameStats
from trench.domain.enums import Position


def team_stats(game: Game, *, home: bool, turnovers: int = 1) -> TeamGameStats:
    return TeamGameStats(
        game_id=game.id,
        team_id=game.home_team_id if home else game.away_team_id,
        offensive_plays=62,
        passing_yards=248,
        rushing_yards=117,
        turnovers=turnovers,
        sacks=3,
    )


async def test_team_stats_by_season(
    repos: Repositories, afc_west: AfcWest, game: Game
) -> None:
    last_season = make_game(afc_west.kc, afc_west.lv, season=SEASON - 1)
    await repos.games.save(last_season)
    current = [team_stats(game, home=True), team_stats(game, home=False)]
    for stats in (*current, team_stats(last_season, home=True)):
        await repos.team_stats.save(stats)

    stored = await repos.team_stats.list_by_season(SEASON)

    assert sorted(stored, key=lambda s: s.team_id) == sorted(
        current, key=lambda s: s.team_id
    )


async def test_team_stats_save_overwrites_same_game_and_team(
    repos: Repositories, game: Game
) -> None:
    await repos.team_stats.save(team_stats(game, home=True, turnovers=1))

    await repos.team_stats.save(team_stats(game, home=True, turnovers=4))

    assert await repos.team_stats.list_by_season(SEASON) == [
        team_stats(game, home=True, turnovers=4)
    ]


async def test_player_stats_by_season(
    repos: Repositories, afc_west: AfcWest, game: Game
) -> None:
    rusher = make_player(afc_west.kc, Position.EDGE, "Edge Rusher")
    await repos.players.save(rusher)
    stats = PlayerGameStats(
        game_id=game.id, player_id=rusher.id, team_id=afc_west.kc.id, sacks=1.5
    )

    await repos.player_stats.save(stats)

    assert await repos.player_stats.list_by_season(SEASON) == [stats]
    assert await repos.player_stats.list_by_season(SEASON - 1) == []


async def test_stats_by_game(
    repos: Repositories, afc_west: AfcWest, game: Game
) -> None:
    other = make_game(afc_west.den, afc_west.lac)
    await repos.games.save(other)
    rusher = make_player(afc_west.kc, Position.EDGE, "Edge Rusher")
    await repos.players.save(rusher)
    home_stats = team_stats(game, home=True)
    player_line = PlayerGameStats(
        game_id=game.id, player_id=rusher.id, team_id=afc_west.kc.id, sacks=1.0
    )
    for stats in (home_stats, team_stats(other, home=True)):
        await repos.team_stats.save(stats)
    await repos.player_stats.save(player_line)

    assert await repos.team_stats.list_by_game(game.id) == [home_stats]
    assert await repos.player_stats.list_by_game(game.id) == [player_line]
    assert await repos.player_stats.list_by_game(other.id) == []
