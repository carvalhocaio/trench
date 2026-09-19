from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, NonNegativeInt

from trench.domain.entities import MAX_WEEK, Score
from trench.domain.enums import Conference, Division, GameStatus


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
