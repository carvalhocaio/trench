from tests.analytics.samples import KC, LV, final
from tests.factories import SEASON, make_game, make_player
from tests.fakes import (
    FakeGameRepository,
    FakePlayerGameStatsRepository,
    FakePlayerRepository,
)
from trench.application.highlights import HighlightsService
from trench.domain.entities import PlayerGameStats
from trench.domain.enums import Position

RUNNER = make_player(KC, Position.RB, "Runner")


async def test_qualifies_rushers_by_final_games_of_their_team() -> None:
    games = FakeGameRepository()
    players = FakePlayerRepository()
    player_stats = FakePlayerGameStatsRepository(games)
    played = final(KC, LV, (24, 17), week=1)
    upcoming = make_game(LV, KC, week=2)
    for game in (played, upcoming):
        await games.save(game)
    await players.save(RUNNER)
    await player_stats.save(
        PlayerGameStats(
            game_id=played.id,
            player_id=RUNNER.id,
            team_id=KC.id,
            rushing_attempts=7,
            rushing_yards=49,
        )
    )
    service = HighlightsService(games=games, players=players, player_stats=player_stats)

    leaders = await service.season(SEASON, limit=3)

    assert [season.player for season in leaders.yards_per_carry] == [RUNNER]
