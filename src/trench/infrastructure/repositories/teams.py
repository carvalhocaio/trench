from uuid import UUID

from sqlalchemy import select

from trench.domain.entities import Team
from trench.infrastructure.models import TeamModel
from trench.infrastructure.repositories.base import SqlRepository


class SqlTeamRepository(SqlRepository[TeamModel, Team]):
    model = TeamModel

    @staticmethod
    def to_entity(model: TeamModel) -> Team:
        return Team(
            id=model.id,
            name=model.name,
            abbreviation=model.abbreviation,
            conference=model.conference,
            division=model.division,
        )

    @staticmethod
    def to_model(entity: Team) -> TeamModel:
        return TeamModel(
            id=entity.id,
            name=entity.name,
            abbreviation=entity.abbreviation,
            conference=entity.conference,
            division=entity.division,
        )

    async def get(self, team_id: UUID) -> Team | None:
        return await self._get(team_id)

    async def get_by_abbreviation(self, abbreviation: str) -> Team | None:
        teams = await self._fetch(
            select(TeamModel).where(TeamModel.abbreviation == abbreviation)
        )
        return teams[0] if teams else None

    async def list_all(self) -> list[Team]:
        return await self._fetch(select(TeamModel).order_by(TeamModel.abbreviation))
