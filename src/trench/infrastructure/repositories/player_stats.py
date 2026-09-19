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
            passing_completions=model.passing_completions,
            passing_attempts=model.passing_attempts,
            passing_yards=model.passing_yards,
            passing_touchdowns=model.passing_touchdowns,
            interceptions_thrown=model.interceptions_thrown,
            rushing_attempts=model.rushing_attempts,
            rushing_yards=model.rushing_yards,
            rushing_touchdowns=model.rushing_touchdowns,
            receiving_targets=model.receiving_targets,
            receptions=model.receptions,
            receiving_yards=model.receiving_yards,
            receiving_touchdowns=model.receiving_touchdowns,
            fumbles=model.fumbles,
            fumbles_lost=model.fumbles_lost,
            tackles=model.tackles,
            tackles_for_loss=model.tackles_for_loss,
            sacks=model.sacks,
            passes_defended=model.passes_defended,
            interceptions=model.interceptions,
            defensive_touchdowns=model.defensive_touchdowns,
            field_goals_made=model.field_goals_made,
            field_goals_attempted=model.field_goals_attempted,
            extra_points_made=model.extra_points_made,
            extra_points_attempted=model.extra_points_attempted,
            punts=model.punts,
            punt_yards=model.punt_yards,
            kick_returns=model.kick_returns,
            kick_return_yards=model.kick_return_yards,
            kick_return_touchdowns=model.kick_return_touchdowns,
            punt_returns=model.punt_returns,
            punt_return_yards=model.punt_return_yards,
            punt_return_touchdowns=model.punt_return_touchdowns,
        )

    @staticmethod
    def to_model(entity: PlayerGameStats) -> PlayerGameStatsModel:
        return PlayerGameStatsModel(
            game_id=entity.game_id,
            player_id=entity.player_id,
            team_id=entity.team_id,
            passing_completions=entity.passing_completions,
            passing_attempts=entity.passing_attempts,
            passing_yards=entity.passing_yards,
            passing_touchdowns=entity.passing_touchdowns,
            interceptions_thrown=entity.interceptions_thrown,
            rushing_attempts=entity.rushing_attempts,
            rushing_yards=entity.rushing_yards,
            rushing_touchdowns=entity.rushing_touchdowns,
            receiving_targets=entity.receiving_targets,
            receptions=entity.receptions,
            receiving_yards=entity.receiving_yards,
            receiving_touchdowns=entity.receiving_touchdowns,
            fumbles=entity.fumbles,
            fumbles_lost=entity.fumbles_lost,
            tackles=entity.tackles,
            tackles_for_loss=entity.tackles_for_loss,
            sacks=entity.sacks,
            passes_defended=entity.passes_defended,
            interceptions=entity.interceptions,
            defensive_touchdowns=entity.defensive_touchdowns,
            field_goals_made=entity.field_goals_made,
            field_goals_attempted=entity.field_goals_attempted,
            extra_points_made=entity.extra_points_made,
            extra_points_attempted=entity.extra_points_attempted,
            punts=entity.punts,
            punt_yards=entity.punt_yards,
            kick_returns=entity.kick_returns,
            kick_return_yards=entity.kick_return_yards,
            kick_return_touchdowns=entity.kick_return_touchdowns,
            punt_returns=entity.punt_returns,
            punt_return_yards=entity.punt_return_yards,
            punt_return_touchdowns=entity.punt_return_touchdowns,
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
