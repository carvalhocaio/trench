from uuid import UUID

from fastapi import APIRouter, status

from trench.api.dependencies import RosterServiceDep
from trench.api.schemas import PlayerPayload, PlayerRead

router = APIRouter(tags=["players"])


@router.post("/players", status_code=status.HTTP_201_CREATED)
async def register_player(
    payload: PlayerPayload, roster: RosterServiceDep
) -> PlayerRead:
    player = await roster.register(**payload.model_dump())
    return PlayerRead.model_validate(player)


@router.get("/players/{player_id}")
async def get_player(player_id: UUID, roster: RosterServiceDep) -> PlayerRead:
    return PlayerRead.model_validate(await roster.get(player_id))


@router.put("/players/{player_id}")
async def update_player(
    player_id: UUID, payload: PlayerPayload, roster: RosterServiceDep
) -> PlayerRead:
    player = await roster.update(player_id, **payload.model_dump())
    return PlayerRead.model_validate(player)


@router.get("/teams/{team_id}/players")
async def list_team_players(
    team_id: UUID, roster: RosterServiceDep
) -> list[PlayerRead]:
    return [PlayerRead.model_validate(p) for p in await roster.list_team(team_id)]
