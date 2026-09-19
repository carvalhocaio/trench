from collections.abc import Collection
from uuid import UUID

from sqlalchemy import select

from trench.domain.entities import Player
from trench.infrastructure.models import PlayerModel
from trench.infrastructure.repositories.base import SqlRepository


class SqlPlayerRepository(SqlRepository[PlayerModel, Player]):
    model = PlayerModel

    @staticmethod
    def to_entity(model: PlayerModel) -> Player:
        return Player(
            id=model.id,
            name=model.name,
            team_id=model.team_id,
            position=model.position,
        )

    @staticmethod
    def to_model(entity: Player) -> PlayerModel:
        return PlayerModel(
            id=entity.id,
            name=entity.name,
            team_id=entity.team_id,
            position=entity.position,
        )

    async def get(self, player_id: UUID) -> Player | None:
        return await self._get(player_id)

    async def get_many(self, player_ids: Collection[UUID]) -> list[Player]:
        if not player_ids:
            return []
        query = (
            select(PlayerModel)
            .where(PlayerModel.id.in_(player_ids))
            .order_by(PlayerModel.name)
        )
        return await self._fetch(query)

    async def list_by_team(self, team_id: UUID) -> list[Player]:
        query = (
            select(PlayerModel)
            .where(PlayerModel.team_id == team_id)
            .order_by(PlayerModel.position, PlayerModel.name)
        )
        return await self._fetch(query)
