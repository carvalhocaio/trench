from uuid import UUID

from fastapi import APIRouter

from trench.api.dependencies import GameStatsServiceDep
from trench.api.schemas import (
    PlayerStatsPayload,
    PlayerStatsRead,
    TeamStatsPayload,
    TeamStatsRead,
)
from trench.domain.entities import TeamGameStats

router = APIRouter(prefix="/games/{game_id}", tags=["stats"])


@router.put("/team-stats/{team_id}")
async def record_team_stats(
    game_id: UUID,
    team_id: UUID,
    payload: TeamStatsPayload,
    stats: GameStatsServiceDep,
) -> TeamStatsRead:
    recorded = await stats.record_team_stats(
        TeamGameStats(game_id=game_id, team_id=team_id, **payload.model_dump())
    )
    return TeamStatsRead.model_validate(recorded)


@router.put("/player-stats/{player_id}")
async def record_player_stats(
    game_id: UUID,
    player_id: UUID,
    payload: PlayerStatsPayload,
    stats: GameStatsServiceDep,
) -> PlayerStatsRead:
    recorded = await stats.record_player_stats(
        game_id=game_id, player_id=player_id, **payload.model_dump()
    )
    return PlayerStatsRead.model_validate(recorded)
