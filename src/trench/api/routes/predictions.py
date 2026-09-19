from uuid import UUID

from fastapi import APIRouter, Query, status

from trench.api.dependencies import PredictionServiceDep
from trench.api.schemas import PredictionRead, SnapshotRead
from trench.domain.entities import MAX_WEEK

router = APIRouter(tags=["predictions"])


@router.get("/predictions")
async def predict_week(
    predictions: PredictionServiceDep,
    season: int,
    week: int = Query(ge=1, le=MAX_WEEK),
) -> list[PredictionRead]:
    week_predictions = await predictions.predict_week(season, week)
    return [PredictionRead.from_prediction(p) for p in week_predictions]


@router.get("/games/{game_id}/prediction")
async def predict_game(
    game_id: UUID, predictions: PredictionServiceDep
) -> PredictionRead:
    return PredictionRead.from_prediction(await predictions.predict(game_id))


@router.post("/games/{game_id}/prediction", status_code=status.HTTP_201_CREATED)
async def record_prediction(
    game_id: UUID, predictions: PredictionServiceDep
) -> PredictionRead:
    return PredictionRead.from_prediction(await predictions.record(game_id))


@router.get("/games/{game_id}/prediction/history")
async def prediction_history(
    game_id: UUID, predictions: PredictionServiceDep
) -> list[SnapshotRead]:
    snapshots = await predictions.history(game_id)
    return [SnapshotRead.model_validate(snapshot) for snapshot in snapshots]
