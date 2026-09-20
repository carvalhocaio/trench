from collections.abc import Iterable, Mapping
from datetime import datetime
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
)

from trench.analytics.calibration import CalibrationReport
from trench.analytics.highlights import PlayerSeason, SeasonLeaders
from trench.analytics.ratings import TeamRating
from trench.api.errors import ErrorCode
from trench.application.predictions import GamePrediction
from trench.application.previews import GamePreview, MatchupPreview
from trench.config import AnalyticsSettings
from trench.domain.entities import MAX_WEEK, Score
from trench.domain.enums import (
    AbsenceStatus,
    Conference,
    Division,
    GameStatus,
    Position,
)


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
    code: ErrorCode


class TeamCreate(_Input):
    name: str = Field(min_length=1, max_length=64)
    abbreviation: str = Field(pattern=r"^[A-Z]{2,4}$")
    conference: Conference
    division: Division


class TeamRead(_Output):
    id: UUID
    name: str
    abbreviation: str
    conference: Conference
    division: Division


class GameCreate(_Input):
    season: int = Field(ge=1920)
    week: int = Field(ge=1, le=MAX_WEEK)
    kickoff: AwareDatetime
    home_team_id: UUID
    away_team_id: UUID


class ScorePayload(_Input):
    home: NonNegativeInt
    away: NonNegativeInt

    def to_domain(self) -> Score:
        return Score(home=self.home, away=self.away)


class ScoreRead(_Output):
    home: int
    away: int


class GameRead(_Output):
    id: UUID
    season: int
    week: int
    kickoff: AwareDatetime
    home_team_id: UUID
    away_team_id: UUID
    status: GameStatus
    score: ScoreRead | None


class PlayerPayload(_Input):
    name: str = Field(min_length=1, max_length=128)
    team_id: UUID
    position: Position


class PlayerRead(_Output):
    id: UUID
    name: str
    team_id: UUID
    position: Position


class TeamStatsPayload(_Input):
    offensive_plays: NonNegativeInt
    passing_yards: int
    rushing_yards: int
    turnovers: NonNegativeInt
    sacks: NonNegativeInt


class TeamStatsRead(_Output):
    game_id: UUID
    team_id: UUID
    offensive_plays: int
    passing_yards: int
    rushing_yards: int
    turnovers: int
    sacks: int
    total_yards: int
    yards_per_play: float | None


class PlayerStatsPayload(_Input):
    passing_completions: NonNegativeInt = 0
    passing_attempts: NonNegativeInt = 0
    passing_yards: int = 0
    passing_touchdowns: NonNegativeInt = 0
    interceptions_thrown: NonNegativeInt = 0
    rushing_attempts: NonNegativeInt = 0
    rushing_yards: int = 0
    rushing_touchdowns: NonNegativeInt = 0
    receiving_targets: NonNegativeInt = 0
    receptions: NonNegativeInt = 0
    receiving_yards: int = 0
    receiving_touchdowns: NonNegativeInt = 0
    fumbles: NonNegativeInt = 0
    fumbles_lost: NonNegativeInt = 0
    tackles: NonNegativeInt = 0
    tackles_for_loss: NonNegativeFloat = Field(default=0.0, multiple_of=0.5)
    sacks: NonNegativeFloat = Field(default=0.0, multiple_of=0.5)
    passes_defended: NonNegativeInt = 0
    interceptions: NonNegativeInt = 0
    defensive_touchdowns: NonNegativeInt = 0
    field_goals_made: NonNegativeInt = 0
    field_goals_attempted: NonNegativeInt = 0
    extra_points_made: NonNegativeInt = 0
    extra_points_attempted: NonNegativeInt = 0
    punts: NonNegativeInt = 0
    punt_yards: int = 0
    kick_returns: NonNegativeInt = 0
    kick_return_yards: int = 0
    kick_return_touchdowns: NonNegativeInt = 0
    punt_returns: NonNegativeInt = 0
    punt_return_yards: int = 0
    punt_return_touchdowns: NonNegativeInt = 0


class PlayerStatsRead(_Output):
    game_id: UUID
    player_id: UUID
    team_id: UUID
    passing_completions: int
    passing_attempts: int
    passing_yards: int
    passing_touchdowns: int
    interceptions_thrown: int
    rushing_attempts: int
    rushing_yards: int
    rushing_touchdowns: int
    receiving_targets: int
    receptions: int
    receiving_yards: int
    receiving_touchdowns: int
    fumbles: int
    fumbles_lost: int
    tackles: int
    tackles_for_loss: float
    sacks: float
    passes_defended: int
    interceptions: int
    defensive_touchdowns: int
    field_goals_made: int
    field_goals_attempted: int
    extra_points_made: int
    extra_points_attempted: int
    punts: int
    punt_yards: int
    kick_returns: int
    kick_return_yards: int
    kick_return_touchdowns: int
    punt_returns: int
    punt_return_yards: int
    punt_return_touchdowns: int
    yards_per_carry: float | None
    yards_per_reception: float | None


class GameStatsRead(_Output):
    team_stats: list[TeamStatsRead]
    player_stats: list[PlayerStatsRead]


class AbsencePayload(_Input):
    status: AbsenceStatus


class AbsenceRead(_Output):
    game_id: UUID
    player_id: UUID
    status: AbsenceStatus


class RatingRead(_Output):
    games_played: int
    wins: int
    losses: int
    ties: int
    points_for_avg: float
    points_against_avg: float
    offense_strength: float
    defense_strength: float


class SideRead(BaseModel):
    team_id: UUID
    projected_points: float
    win_probability: float
    rating: RatingRead


class AbsenceImpactRead(BaseModel):
    player: PlayerRead
    status: AbsenceStatus
    affected_team_id: UUID
    points_delta: float


class PredictionRead(BaseModel):
    game: GameRead
    as_of: datetime
    spread: float
    home: SideRead
    away: SideRead
    absences: list[AbsenceImpactRead]

    @classmethod
    def from_prediction(cls, prediction: GamePrediction) -> PredictionRead:
        game, projection = prediction.game, prediction.projection
        return cls(
            game=GameRead.model_validate(game),
            as_of=prediction.as_of,
            spread=projection.spread,
            home=_side(
                game.home_team_id,
                projection.home_points,
                projection.home_win_probability,
                prediction.home_rating,
            ),
            away=_side(
                game.away_team_id,
                projection.away_points,
                projection.away_win_probability,
                prediction.away_rating,
            ),
            absences=[
                AbsenceImpactRead(
                    player=PlayerRead.model_validate(impact.player),
                    status=impact.status,
                    affected_team_id=(
                        game.home_team_id
                        if impact.applies_to_home
                        else game.away_team_id
                    ),
                    points_delta=impact.points_delta,
                )
                for impact in prediction.absences.impacts
            ],
        )


class SnapshotRead(_Output):
    id: UUID
    game_id: UUID
    as_of: datetime
    home_projected_points: float
    away_projected_points: float
    home_win_probability: float
    away_win_probability: float
    projected_spread: float
    model_version: str


def _side(
    team_id: UUID, points: float, probability: float, rating: TeamRating
) -> SideRead:
    return SideRead(
        team_id=team_id,
        projected_points=points,
        win_probability=probability,
        rating=RatingRead.model_validate(rating),
    )


class PlayerSeasonRead(_Output):
    player: PlayerRead
    games: int
    passing_yards: int
    passing_touchdowns: int
    interceptions_thrown: int
    rushing_attempts: int
    rushing_yards: int
    rushing_touchdowns: int
    interceptions: int
    yards_per_carry: float | None
    sacks: float


class HighlightsRead(BaseModel):
    season: int
    passing_yards: list[PlayerSeasonRead]
    passing_touchdowns: list[PlayerSeasonRead]
    rushing_touchdowns_qb: list[PlayerSeasonRead]
    yards_per_carry: list[PlayerSeasonRead]
    sacks: list[PlayerSeasonRead]
    interceptions: list[PlayerSeasonRead]

    @classmethod
    def from_leaders(cls, season: int, leaders: SeasonLeaders) -> HighlightsRead:
        def rows(seasons: Iterable[PlayerSeason]) -> list[PlayerSeasonRead]:
            return [PlayerSeasonRead.model_validate(s) for s in seasons]

        return cls(
            season=season,
            passing_yards=rows(leaders.passing_yards),
            passing_touchdowns=rows(leaders.passing_touchdowns),
            rushing_touchdowns_qb=rows(leaders.rushing_touchdowns_qb),
            yards_per_carry=rows(leaders.yards_per_carry),
            sacks=rows(leaders.sacks),
            interceptions=rows(leaders.interceptions),
        )


class PreviewRead(BaseModel):
    prediction: PredictionRead
    preview: MatchupPreview

    @classmethod
    def from_preview(cls, game_preview: GamePreview) -> PreviewRead:
        return cls(
            prediction=PredictionRead.from_prediction(game_preview.prediction),
            preview=game_preview.preview,
        )


class ReliabilityBinRead(_Output):
    lower: float
    upper: float
    forecasts: int
    mean_probability: float
    observed_rate: float


class CalibrationReportRead(_Output):
    forecasts: int
    brier_score: float
    log_loss: float
    favorite_accuracy: float
    reliability: list[ReliabilityBinRead]


class CalibrationParametersRead(_Output):
    shrinkage_games: float
    home_field_advantage: float
    score_margin_stddev: float
    efficiency_weight: float
    efficiency_shrinkage_games: float


class LiveCalibrationRead(BaseModel):
    model_version: str
    report: CalibrationReportRead


class CalibrationRead(BaseModel):
    season: int
    parameters: CalibrationParametersRead
    backtest: CalibrationReportRead | None
    live: list[LiveCalibrationRead]

    @classmethod
    def build(
        cls,
        *,
        season: int,
        settings: AnalyticsSettings,
        backtest: CalibrationReport | None,
        live: Mapping[str, CalibrationReport],
    ) -> CalibrationRead:
        return cls(
            season=season,
            parameters=CalibrationParametersRead.model_validate(settings),
            backtest=(
                CalibrationReportRead.model_validate(backtest) if backtest else None
            ),
            live=[
                LiveCalibrationRead(
                    model_version=version,
                    report=CalibrationReportRead.model_validate(report),
                )
                for version, report in live.items()
            ],
        )
