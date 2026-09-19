from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from trench.infrastructure.models import Base


class SqlRepository[ModelT: Base, EntityT](ABC):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    @abstractmethod
    def to_entity(model: ModelT) -> EntityT: ...

    @staticmethod
    @abstractmethod
    def to_model(entity: EntityT) -> ModelT: ...

    async def save(self, entity: EntityT, /) -> None:
        await self._session.merge(self.to_model(entity))
        await self._session.flush()

    async def _get(self, key: Any) -> EntityT | None:
        model = await self._session.get(self.model, key)
        return self.to_entity(model) if model else None

    async def _fetch(self, query: Select[tuple[ModelT]]) -> list[EntityT]:
        models = await self._session.scalars(query)
        return [self.to_entity(model) for model in models]
