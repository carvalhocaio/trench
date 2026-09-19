from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
)

from trench.domain.entities import MAX_WEEK, Score
from trench.domain.enums import Conference, Division, GameStatus, Position


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


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
    passing_touchdowns: NonNegativeInt = 0
    rushing_attempts: NonNegativeInt = 0
    rushing_yards: int = 0
    sacks: NonNegativeFloat = Field(default=0.0, multiple_of=0.5)


class PlayerStatsRead(_Output):
    game_id: UUID
    player_id: UUID
    team_id: UUID
    passing_touchdowns: int
    rushing_attempts: int
    rushing_yards: int
    sacks: float
    yards_per_carry: float | None
