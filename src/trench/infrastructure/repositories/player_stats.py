from uuid import UUID

from sqlalchemy import select

from trench.domain.entities import PlayerGameStats
from trench.infrastructure.models import GameModel, PlayerGameStatsModel
from trench.infrastructure.repositories.base import SqlRepository


class SqlPlayerGameStatsRepository(
    SqlRepository[PlayerGameStatsModel, PlayerGameStats]
):
    model = PlayerGameStatsModel

    @staticmethod
    def to_entity(model: PlayerGameStatsModel) -> PlayerGameStats:
        return PlayerGameStats(
            game_id=model.game_id,
            player_id=model.player_id,
            team_id=model.team_id,
            passing_touchdowns=model.passing_touchdowns,
            rushing_attempts=model.rushing_attempts,
            rushing_yards=model.rushing_yards,
            sacks=model.sacks,
        )

    @staticmethod
    def to_model(entity: PlayerGameStats) -> PlayerGameStatsModel:
        return PlayerGameStatsModel(
            game_id=entity.game_id,
            player_id=entity.player_id,
            team_id=entity.team_id,
            passing_touchdowns=entity.passing_touchdowns,
            rushing_attempts=entity.rushing_attempts,
            rushing_yards=entity.rushing_yards,
            sacks=entity.sacks,
        )

    async def list_by_game(self, game_id: UUID) -> list[PlayerGameStats]:
        query = (
            select(PlayerGameStatsModel)
            .where(PlayerGameStatsModel.game_id == game_id)
            .order_by(PlayerGameStatsModel.player_id)
        )
        return await self._fetch(query)

    async def list_by_season(self, season: int) -> list[PlayerGameStats]:
        query = (
            select(PlayerGameStatsModel)
            .join(GameModel, GameModel.id == PlayerGameStatsModel.game_id)
            .where(GameModel.season == season)
            .order_by(GameModel.kickoff, PlayerGameStatsModel.player_id)
        )
        return await self._fetch(query)
