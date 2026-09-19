from uuid import UUID

from trench.application.lookups import (
    require_game,
    require_participant,
    require_player,
)
from trench.domain.entities import PlayerGameStats, TeamGameStats
from trench.domain.repositories import (
    GameRepository,
    PlayerGameStatsRepository,
    PlayerRepository,
    TeamGameStatsRepository,
)


class GameStatsService:
    def __init__(
        self,
        *,
        games: GameRepository,
        players: PlayerRepository,
        team_stats: TeamGameStatsRepository,
        player_stats: PlayerGameStatsRepository,
    ) -> None:
        self._games = games
        self._players = players
        self._team_stats = team_stats
        self._player_stats = player_stats

    async def record_team_stats(self, stats: TeamGameStats) -> TeamGameStats:
        game = await require_game(self._games, stats.game_id)
        require_participant(game, stats.team_id)
        await self._team_stats.save(stats)
        return stats

    async def record_player_stats(
        self,
        *,
        game_id: UUID,
        player_id: UUID,
        passing_touchdowns: int,
        rushing_attempts: int,
        rushing_yards: int,
        sacks: float,
    ) -> PlayerGameStats:
        game = await require_game(self._games, game_id)
        player = await require_player(self._players, player_id)
        require_participant(game, player.team_id)
        stats = PlayerGameStats(
            game_id=game.id,
            player_id=player.id,
            team_id=player.team_id,
            passing_touchdowns=passing_touchdowns,
            rushing_attempts=rushing_attempts,
            rushing_yards=rushing_yards,
            sacks=sacks,
        )
        await self._player_stats.save(stats)
        return stats
