from uuid import UUID

from fastapi import APIRouter, Query, status

from trench.api.dependencies import ScheduleServiceDep
from trench.api.schemas import ErrorResponse, GameCreate, GameRead, ScorePayload
from trench.domain.entities import MAX_WEEK

router = APIRouter(prefix="/games", tags=["games"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, responses={409: {"model": ErrorResponse}}
)
async def schedule_game(payload: GameCreate, schedule: ScheduleServiceDep) -> GameRead:
    game = await schedule.schedule(**payload.model_dump())
    return GameRead.model_validate(game)


@router.get("")
async def list_games(
    schedule: ScheduleServiceDep,
    season: int,
    week: int | None = Query(default=None, ge=1, le=MAX_WEEK),
    team_id: UUID | None = None,
) -> list[GameRead]:
    games = await schedule.find(season, week=week, team_id=team_id)
    return [GameRead.model_validate(game) for game in games]


@router.get("/{game_id}", responses={404: {"model": ErrorResponse}})
async def get_game(game_id: UUID, schedule: ScheduleServiceDep) -> GameRead:
    return GameRead.model_validate(await schedule.get(game_id))


@router.put(
    "/{game_id}/score",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def record_score(
    game_id: UUID, payload: ScorePayload, schedule: ScheduleServiceDep
) -> GameRead:
    game = await schedule.record_score(game_id, payload.to_domain())
    return GameRead.model_validate(game)
