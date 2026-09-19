from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from trench.analytics.absences import AbsenceReport, assess_absences
from trench.analytics.projection import Projection, project_game
from trench.analytics.ratings import TeamRating, compute_ratings
from trench.application.lookups import require_game
from trench.config import AnalyticsSettings
from trench.domain.entities import Game, Player, PredictionSnapshot
from trench.domain.repositories import (
    AbsenceRepository,
    GameRepository,
    PlayerRepository,
    PredictionSnapshotRepository,
)

MODEL_VERSION = "0.1.0"

type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True, kw_only=True)
class GamePrediction:
    game: Game
    home_rating: TeamRating
    away_rating: TeamRating
    absences: AbsenceReport
    projection: Projection
    as_of: datetime

    def to_snapshot(self) -> PredictionSnapshot:
        return PredictionSnapshot(
            game_id=self.game.id,
            as_of=self.as_of,
            home_projected_points=self.projection.home_points,
            away_projected_points=self.projection.away_points,
            home_win_probability=self.projection.home_win_probability,
            model_version=MODEL_VERSION,
        )


class PredictionService:
    def __init__(
        self,
        *,
        games: GameRepository,
        players: PlayerRepository,
        absences: AbsenceRepository,
        snapshots: PredictionSnapshotRepository,
        settings: AnalyticsSettings,
        clock: Clock = utc_now,
    ) -> None:
        self._games = games
        self._players = players
        self._absences = absences
        self._snapshots = snapshots
        self._settings = settings
        self._clock = clock

    async def predict(self, game_id: UUID) -> GamePrediction:
        game = await require_game(self._games, game_id)
        season_games = await self._games.list_by_season(game.season)
        return await self._predict(game, season_games)

    async def predict_week(self, season: int, week: int) -> list[GamePrediction]:
        season_games = await self._games.list_by_season(season)
        return [
            await self._predict(game, season_games)
            for game in season_games
            if game.week == week
        ]

    async def history(self, game_id: UUID) -> list[PredictionSnapshot]:
        await require_game(self._games, game_id)
        return await self._snapshots.list_by_game(game_id)

    async def record(self, game_id: UUID) -> GamePrediction:
        prediction = await self.predict(game_id)
        await self._snapshots.save(prediction.to_snapshot())
        return prediction

    async def _predict(
        self, game: Game, season_games: Sequence[Game]
    ) -> GamePrediction:
        previous_games = [g for g in season_games if g.kickoff < game.kickoff]
        ratings = compute_ratings(
            previous_games, shrinkage_games=self._settings.shrinkage_games
        )
        report = assess_absences(
            game,
            await self._absences.list_by_game(game.id),
            await self._rosters(game),
            position_weights=self._settings.position_weights,
            absence_probabilities=self._settings.absence_probabilities,
        )
        projection = project_game(
            ratings,
            home_team_id=game.home_team_id,
            away_team_id=game.away_team_id,
            home_field_advantage=self._settings.home_field_advantage,
            score_margin_stddev=self._settings.score_margin_stddev,
            adjustment=report.adjustment,
        )
        return GamePrediction(
            game=game,
            home_rating=ratings.rating_for(game.home_team_id),
            away_rating=ratings.rating_for(game.away_team_id),
            absences=report,
            projection=projection,
            as_of=self._clock(),
        )

    async def _rosters(self, game: Game) -> dict[UUID, Player]:
        return {
            player.id: player
            for team_id in (game.home_team_id, game.away_team_id)
            for player in await self._players.list_by_team(team_id)
        }
