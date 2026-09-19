from uuid import UUID

from fastapi import APIRouter, Query, status

from trench.api.dependencies import PredictionServiceDep, PreviewServiceDep
from trench.api.schemas import ErrorResponse, PredictionRead, PreviewRead, SnapshotRead
from trench.domain.entities import MAX_WEEK

router = APIRouter(tags=["predictions"])


@router.get("/predictions", responses={409: {"model": ErrorResponse}})
async def predict_week(
    predictions: PredictionServiceDep,
    season: int,
    week: int = Query(ge=1, le=MAX_WEEK),
) -> list[PredictionRead]:
    week_predictions = await predictions.predict_week(season, week)
    return [PredictionRead.from_prediction(p) for p in week_predictions]


@router.get(
    "/games/{game_id}/prediction",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def predict_game(
    game_id: UUID, predictions: PredictionServiceDep
) -> PredictionRead:
    return PredictionRead.from_prediction(await predictions.predict(game_id))


@router.post(
    "/games/{game_id}/prediction",
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def record_prediction(
    game_id: UUID, predictions: PredictionServiceDep
) -> PredictionRead:
    return PredictionRead.from_prediction(await predictions.record(game_id))


@router.get(
    "/games/{game_id}/prediction/history", responses={404: {"model": ErrorResponse}}
)
async def prediction_history(
    game_id: UUID, predictions: PredictionServiceDep
) -> list[SnapshotRead]:
    snapshots = await predictions.history(game_id)
    return [SnapshotRead.model_validate(snapshot) for snapshot in snapshots]


@router.get(
    "/games/{game_id}/preview",
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def preview_game(game_id: UUID, previews: PreviewServiceDep) -> PreviewRead:
    return PreviewRead.from_preview(await previews.preview(game_id))
