from dataclasses import dataclass
from uuid import UUID

from trench.application.clock import Clock, utc_now
from trench.application.lookups import (
    require_game,
    require_participant,
    require_player,
)
from trench.domain.entities import Game, PlayerGameStats, TeamGameStats
from trench.domain.errors import GameNotStartedError
from trench.domain.repositories import (
    GameRepository,
    PlayerGameStatsRepository,
    PlayerRepository,
    TeamGameStatsRepository,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GameStats:
    team_stats: list[TeamGameStats]
    player_stats: list[PlayerGameStats]


class GameStatsService:
    def __init__(
        self,
        *,
        games: GameRepository,
        players: PlayerRepository,
        team_stats: TeamGameStatsRepository,
        player_stats: PlayerGameStatsRepository,
        clock: Clock = utc_now,
    ) -> None:
        self._games = games
        self._players = players
        self._team_stats = team_stats
        self._player_stats = player_stats
        self._clock = clock

    async def of_game(self, game_id: UUID) -> GameStats:
        game = await require_game(self._games, game_id)
        return GameStats(
            team_stats=await self._team_stats.list_by_game(game.id),
            player_stats=await self._player_stats.list_by_game(game.id),
        )

    async def record_team_stats(self, stats: TeamGameStats) -> TeamGameStats:
        game = await require_game(self._games, stats.game_id)
        require_participant(game, stats.team_id)
        self._require_started(game)
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
        self._require_started(game)
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

    def _require_started(self, game: Game) -> None:
        at = self._clock()
        if not game.has_started(at):
            raise GameNotStartedError(game.id, game.kickoff)
