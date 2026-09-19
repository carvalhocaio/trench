from uuid import UUID

from sqlalchemy import select

from trench.domain.entities import TeamGameStats
from trench.infrastructure.models import GameModel, TeamGameStatsModel
from trench.infrastructure.repositories.base import SqlRepository


class SqlTeamGameStatsRepository(SqlRepository[TeamGameStatsModel, TeamGameStats]):
    model = TeamGameStatsModel

    @staticmethod
    def to_entity(model: TeamGameStatsModel) -> TeamGameStats:
        return TeamGameStats(
            game_id=model.game_id,
            team_id=model.team_id,
            offensive_plays=model.offensive_plays,
            passing_yards=model.passing_yards,
            rushing_yards=model.rushing_yards,
            turnovers=model.turnovers,
            sacks=model.sacks,
        )

    @staticmethod
    def to_model(entity: TeamGameStats) -> TeamGameStatsModel:
        return TeamGameStatsModel(
            game_id=entity.game_id,
            team_id=entity.team_id,
            offensive_plays=entity.offensive_plays,
            passing_yards=entity.passing_yards,
            rushing_yards=entity.rushing_yards,
            turnovers=entity.turnovers,
            sacks=entity.sacks,
        )

    async def list_by_game(self, game_id: UUID) -> list[TeamGameStats]:
        query = (
            select(TeamGameStatsModel)
            .where(TeamGameStatsModel.game_id == game_id)
            .order_by(TeamGameStatsModel.team_id)
        )
        return await self._fetch(query)

    async def list_by_season(self, season: int) -> list[TeamGameStats]:
        query = (
            select(TeamGameStatsModel)
            .join(GameModel, GameModel.id == TeamGameStatsModel.game_id)
            .where(GameModel.season == season)
            .order_by(GameModel.kickoff, TeamGameStatsModel.team_id)
        )
        return await self._fetch(query)
