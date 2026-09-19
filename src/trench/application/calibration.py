from collections import defaultdict
from collections.abc import Iterable, Mapping
from uuid import UUID

from trench.analytics.calibration import CalibrationReport, Forecast, evaluate
from trench.analytics.errors import InsufficientDataError
from trench.application.predictions import PredictionService
from trench.domain.entities import Game, PredictionSnapshot
from trench.domain.repositories import GameRepository, PredictionSnapshotRepository


class CalibrationService:
    def __init__(
        self,
        *,
        predictions: PredictionService,
        games: GameRepository,
        snapshots: PredictionSnapshotRepository,
    ) -> None:
        self._predictions = predictions
        self._games = games
        self._snapshots = snapshots

    async def backtest(self, season: int) -> CalibrationReport | None:
        forecasts = [
            Forecast(prediction.projection.home_win_probability, home_won)
            for prediction in await self._predictions.predict_played(season)
            if (home_won := _home_won(prediction.game)) is not None
        ]
        return _evaluate_or_none(forecasts)

    async def live(self, season: int) -> dict[str, CalibrationReport]:
        games = {game.id: game for game in await self._games.list_by_season(season)}
        by_version: dict[str, list[Forecast]] = defaultdict(list)
        for snapshot in _last_before_kickoff(
            await self._snapshots.list_by_season(season), games
        ):
            home_won = _home_won(games[snapshot.game_id])
            if home_won is not None:
                by_version[snapshot.model_version].append(
                    Forecast(snapshot.home_win_probability, home_won)
                )
        return {
            version: evaluate(forecasts)
            for version, forecasts in sorted(by_version.items())
        }


def _home_won(game: Game) -> bool | None:
    if game.score is None or game.score.home == game.score.away:
        return None
    return game.score.home > game.score.away


def _last_before_kickoff(
    snapshots: Iterable[PredictionSnapshot], games: Mapping[UUID, Game]
) -> list[PredictionSnapshot]:
    latest: dict[tuple[UUID, str], PredictionSnapshot] = {}
    for snapshot in snapshots:
        if snapshot.as_of >= games[snapshot.game_id].kickoff:
            continue
        key = (snapshot.game_id, snapshot.model_version)
        if key not in latest or snapshot.as_of > latest[key].as_of:
            latest[key] = snapshot
    return list(latest.values())


def _evaluate_or_none(forecasts: list[Forecast]) -> CalibrationReport | None:
    try:
        return evaluate(forecasts)
    except InsufficientDataError:
        return None
