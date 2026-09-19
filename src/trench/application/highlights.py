from collections import Counter

from trench.analytics.highlights import (
    SeasonLeaders,
    aggregate_seasons,
    season_leaders,
)
from trench.domain.enums import GameStatus
from trench.domain.repositories import (
    GameRepository,
    PlayerGameStatsRepository,
    PlayerRepository,
)


class HighlightsService:
    def __init__(
        self,
        *,
        games: GameRepository,
        players: PlayerRepository,
        player_stats: PlayerGameStatsRepository,
    ) -> None:
        self._games = games
        self._players = players
        self._player_stats = player_stats

    async def season(self, season: int, *, limit: int) -> SeasonLeaders:
        stats = await self._player_stats.list_by_season(season)
        players = await self._players.get_many({line.player_id for line in stats})
        team_games = Counter(
            team_id
            for game in await self._games.list_by_season(season)
            if game.status is GameStatus.FINAL
            for team_id in (game.home_team_id, game.away_team_id)
        )
        return season_leaders(
            aggregate_seasons(stats, {player.id: player for player in players}),
            team_games=team_games,
            limit=limit,
        )
