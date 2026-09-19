from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trench.domain.entities import Team
from trench.infrastructure.models import TeamModel


def _to_entity(model: TeamModel) -> Team:
    return Team(
        id=model.id,
        name=model.name,
        abbreviation=model.abbreviation,
        conference=model.conference,
        division=model.division,
    )


def _to_model(team: Team) -> TeamModel:
    return TeamModel(
        id=team.id,
        name=team.name,
        abbreviation=team.abbreviation,
        conference=team.conference,
        division=team.division,
    )


class SqlTeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, team: Team) -> None:
        await self._session.merge(_to_model(team))
        await self._session.flush()

    async def get(self, team_id: UUID) -> Team | None:
        model = await self._session.get(TeamModel, team_id)
        return _to_entity(model) if model else None

    async def get_by_abbreviation(self, abbreviation: str) -> Team | None:
        model = await self._session.scalar(
            select(TeamModel).where(TeamModel.abbreviation == abbreviation)
        )
        return _to_entity(model) if model else None

    async def list_all(self) -> list[Team]:
        models = await self._session.scalars(
            select(TeamModel).order_by(TeamModel.abbreviation)
        )
        return [_to_entity(model) for model in models]
