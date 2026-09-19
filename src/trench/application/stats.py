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
        passing_completions: int = 0,
        passing_attempts: int = 0,
        passing_yards: int = 0,
        passing_touchdowns: int = 0,
        interceptions_thrown: int = 0,
        rushing_attempts: int = 0,
        rushing_yards: int = 0,
        rushing_touchdowns: int = 0,
        receiving_targets: int = 0,
        receptions: int = 0,
        receiving_yards: int = 0,
        receiving_touchdowns: int = 0,
        fumbles: int = 0,
        fumbles_lost: int = 0,
        tackles: int = 0,
        tackles_for_loss: float = 0.0,
        sacks: float = 0.0,
        passes_defended: int = 0,
        interceptions: int = 0,
        defensive_touchdowns: int = 0,
        field_goals_made: int = 0,
        field_goals_attempted: int = 0,
        extra_points_made: int = 0,
        extra_points_attempted: int = 0,
        punts: int = 0,
        punt_yards: int = 0,
        kick_returns: int = 0,
        kick_return_yards: int = 0,
        kick_return_touchdowns: int = 0,
        punt_returns: int = 0,
        punt_return_yards: int = 0,
        punt_return_touchdowns: int = 0,
    ) -> PlayerGameStats:
        game = await require_game(self._games, game_id)
        player = await require_player(self._players, player_id)
        require_participant(game, player.team_id)
        self._require_started(game)
        stats = PlayerGameStats(
            game_id=game.id,
            player_id=player.id,
            team_id=player.team_id,
            passing_completions=passing_completions,
            passing_attempts=passing_attempts,
            passing_yards=passing_yards,
            passing_touchdowns=passing_touchdowns,
            interceptions_thrown=interceptions_thrown,
            rushing_attempts=rushing_attempts,
            rushing_yards=rushing_yards,
            rushing_touchdowns=rushing_touchdowns,
            receiving_targets=receiving_targets,
            receptions=receptions,
            receiving_yards=receiving_yards,
            receiving_touchdowns=receiving_touchdowns,
            fumbles=fumbles,
            fumbles_lost=fumbles_lost,
            tackles=tackles,
            tackles_for_loss=tackles_for_loss,
            sacks=sacks,
            passes_defended=passes_defended,
            interceptions=interceptions,
            defensive_touchdowns=defensive_touchdowns,
            field_goals_made=field_goals_made,
            field_goals_attempted=field_goals_attempted,
            extra_points_made=extra_points_made,
            extra_points_attempted=extra_points_attempted,
            punts=punts,
            punt_yards=punt_yards,
            kick_returns=kick_returns,
            kick_return_yards=kick_return_yards,
            kick_return_touchdowns=kick_return_touchdowns,
            punt_returns=punt_returns,
            punt_return_yards=punt_return_yards,
            punt_return_touchdowns=punt_return_touchdowns,
        )
        await self._player_stats.save(stats)
        return stats

    def _require_started(self, game: Game) -> None:
        at = self._clock()
        if not game.has_started(at):
            raise GameNotStartedError(game.id, game.kickoff)
