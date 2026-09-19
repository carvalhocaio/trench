from uuid import UUID

from sqlalchemy import select

from trench.domain.entities import PredictionSnapshot
from trench.infrastructure.models import GameModel, PredictionSnapshotModel
from trench.infrastructure.repositories.base import SqlRepository


class SqlPredictionSnapshotRepository(
    SqlRepository[PredictionSnapshotModel, PredictionSnapshot]
):
    model = PredictionSnapshotModel

    @staticmethod
    def to_entity(model: PredictionSnapshotModel) -> PredictionSnapshot:
        return PredictionSnapshot(
            id=model.id,
            game_id=model.game_id,
            as_of=model.as_of,
            home_projected_points=model.home_projected_points,
            away_projected_points=model.away_projected_points,
            home_win_probability=model.home_win_probability,
            model_version=model.model_version,
        )

    @staticmethod
    def to_model(entity: PredictionSnapshot) -> PredictionSnapshotModel:
        return PredictionSnapshotModel(
            id=entity.id,
            game_id=entity.game_id,
            as_of=entity.as_of,
            home_projected_points=entity.home_projected_points,
            away_projected_points=entity.away_projected_points,
            home_win_probability=entity.home_win_probability,
            model_version=entity.model_version,
        )

    async def list_by_game(self, game_id: UUID) -> list[PredictionSnapshot]:
        query = (
            select(PredictionSnapshotModel)
            .where(PredictionSnapshotModel.game_id == game_id)
            .order_by(PredictionSnapshotModel.as_of)
        )
        return await self._fetch(query)

    async def list_by_season(self, season: int) -> list[PredictionSnapshot]:
        query = (
            select(PredictionSnapshotModel)
            .join(GameModel, GameModel.id == PredictionSnapshotModel.game_id)
            .where(GameModel.season == season)
            .order_by(GameModel.kickoff, PredictionSnapshotModel.as_of)
        )
        return await self._fetch(query)
