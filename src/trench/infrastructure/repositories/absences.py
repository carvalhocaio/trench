from uuid import UUID

from sqlalchemy import delete, select

from trench.domain.entities import Absence
from trench.infrastructure.models import AbsenceModel
from trench.infrastructure.repositories.base import SqlRepository


class SqlAbsenceRepository(SqlRepository[AbsenceModel, Absence]):
    model = AbsenceModel

    @staticmethod
    def to_entity(model: AbsenceModel) -> Absence:
        return Absence(
            game_id=model.game_id,
            player_id=model.player_id,
            status=model.status,
        )

    @staticmethod
    def to_model(entity: Absence) -> AbsenceModel:
        return AbsenceModel(
            game_id=entity.game_id,
            player_id=entity.player_id,
            status=entity.status,
        )

    async def remove(self, game_id: UUID, player_id: UUID) -> None:
        await self._session.execute(
            delete(AbsenceModel).where(
                AbsenceModel.game_id == game_id,
                AbsenceModel.player_id == player_id,
            )
        )

    async def list_by_game(self, game_id: UUID) -> list[Absence]:
        query = (
            select(AbsenceModel)
            .where(AbsenceModel.game_id == game_id)
            .order_by(AbsenceModel.player_id)
        )
        return await self._fetch(query)
