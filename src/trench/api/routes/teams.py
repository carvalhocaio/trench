from uuid import UUID

from fastapi import APIRouter, status

from trench.api.dependencies import TeamRepositoryDep
from trench.api.schemas import TeamCreate, TeamRead
from trench.application.errors import TeamNotFoundError
from trench.domain.entities import Team

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_team(payload: TeamCreate, teams: TeamRepositoryDep) -> TeamRead:
    team = Team(**payload.model_dump())
    await teams.save(team)
    return TeamRead.model_validate(team)


@router.get("")
async def list_teams(teams: TeamRepositoryDep) -> list[TeamRead]:
    return [TeamRead.model_validate(team) for team in await teams.list_all()]


@router.get("/{team_id}")
async def get_team(team_id: UUID, teams: TeamRepositoryDep) -> TeamRead:
    team = await teams.get(team_id)
    if team is None:
        raise TeamNotFoundError(team_id)
    return TeamRead.model_validate(team)
