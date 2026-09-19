from dataclasses import dataclass, field, replace
from datetime import datetime
from uuid import UUID, uuid7

from trench.domain.enums import (
    AbsenceStatus,
    Conference,
    Division,
    GameStatus,
    Position,
)
from trench.domain.errors import DomainValidationError, GameNotStartedError

MAX_WEEK = 18


def _require_non_negative(**values: float) -> None:
    negatives = [name for name, value in values.items() if value < 0]
    if negatives:
        raise DomainValidationError(f"must be non-negative: {', '.join(negatives)}")


def _require_timezone_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise DomainValidationError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True, kw_only=True)
class Team:
    id: UUID = field(default_factory=uuid7)
    name: str
    abbreviation: str
    conference: Conference
    division: Division


@dataclass(frozen=True, slots=True, kw_only=True)
class Score:
    home: int
    away: int

    def __post_init__(self) -> None:
        _require_non_negative(home=self.home, away=self.away)


@dataclass(frozen=True, slots=True, kw_only=True)
class Game:
    id: UUID = field(default_factory=uuid7)
    season: int
    week: int
    kickoff: datetime
    home_team_id: UUID
    away_team_id: UUID
    score: Score | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.week <= MAX_WEEK:
            raise DomainValidationError(f"week must be between 1 and {MAX_WEEK}")
        if self.home_team_id == self.away_team_id:
            raise DomainValidationError("a team cannot play against itself")
        _require_timezone_aware("kickoff", self.kickoff)

    @property
    def status(self) -> GameStatus:
        return GameStatus.SCHEDULED if self.score is None else GameStatus.FINAL

    def has_started(self, at: datetime) -> bool:
        return at >= self.kickoff

    def finalize(self, score: Score, *, at: datetime) -> Game:
        if not self.has_started(at):
            raise GameNotStartedError(self.id, self.kickoff)
        return replace(self, score=score)

    def involves(self, team_id: UUID) -> bool:
        return team_id in (self.home_team_id, self.away_team_id)

    def is_home(self, team_id: UUID) -> bool:
        self._require_participant(team_id)
        return team_id == self.home_team_id

    def opponent_of(self, team_id: UUID) -> UUID:
        return self.away_team_id if self.is_home(team_id) else self.home_team_id

    def points_for(self, team_id: UUID) -> int:
        score = self._require_score()
        return score.home if self.is_home(team_id) else score.away

    def points_against(self, team_id: UUID) -> int:
        return self.points_for(self.opponent_of(team_id))

    def winner_id(self) -> UUID | None:
        score = self._require_score()
        if score.home == score.away:
            return None
        return self.home_team_id if score.home > score.away else self.away_team_id

    def _require_participant(self, team_id: UUID) -> None:
        if not self.involves(team_id):
            raise DomainValidationError(f"team {team_id} is not part of game {self.id}")

    def _require_score(self) -> Score:
        if self.score is None:
            raise DomainValidationError(f"game {self.id} has no final score yet")
        return self.score


@dataclass(frozen=True, slots=True, kw_only=True)
class TeamGameStats:
    game_id: UUID
    team_id: UUID
    offensive_plays: int
    passing_yards: int
    rushing_yards: int
    turnovers: int
    sacks: int

    def __post_init__(self) -> None:
        _require_non_negative(
            offensive_plays=self.offensive_plays,
            turnovers=self.turnovers,
            sacks=self.sacks,
        )

    @property
    def total_yards(self) -> int:
        return self.passing_yards + self.rushing_yards

    @property
    def yards_per_play(self) -> float | None:
        if self.offensive_plays == 0:
            return None
        return self.total_yards / self.offensive_plays


@dataclass(frozen=True, slots=True, kw_only=True)
class Player:
    id: UUID = field(default_factory=uuid7)
    name: str
    team_id: UUID
    position: Position


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerGameStats:
    game_id: UUID
    player_id: UUID
    team_id: UUID
    passing_completions: int = 0
    passing_attempts: int = 0
    passing_yards: int = 0
    passing_touchdowns: int = 0
    interceptions_thrown: int = 0
    rushing_attempts: int = 0
    rushing_yards: int = 0
    rushing_touchdowns: int = 0
    receiving_targets: int = 0
    receptions: int = 0
    receiving_yards: int = 0
    receiving_touchdowns: int = 0
    fumbles: int = 0
    fumbles_lost: int = 0
    tackles: int = 0
    tackles_for_loss: float = 0.0
    sacks: float = 0.0
    passes_defended: int = 0
    interceptions: int = 0
    defensive_touchdowns: int = 0
    field_goals_made: int = 0
    field_goals_attempted: int = 0
    extra_points_made: int = 0
    extra_points_attempted: int = 0
    punts: int = 0
    punt_yards: int = 0
    kick_returns: int = 0
    kick_return_yards: int = 0
    kick_return_touchdowns: int = 0
    punt_returns: int = 0
    punt_return_yards: int = 0
    punt_return_touchdowns: int = 0

    def __post_init__(self) -> None:
        _require_non_negative(
            passing_completions=self.passing_completions,
            passing_attempts=self.passing_attempts,
            passing_touchdowns=self.passing_touchdowns,
            interceptions_thrown=self.interceptions_thrown,
            rushing_attempts=self.rushing_attempts,
            rushing_touchdowns=self.rushing_touchdowns,
            receiving_targets=self.receiving_targets,
            receptions=self.receptions,
            receiving_touchdowns=self.receiving_touchdowns,
            fumbles=self.fumbles,
            fumbles_lost=self.fumbles_lost,
            tackles=self.tackles,
            tackles_for_loss=self.tackles_for_loss,
            sacks=self.sacks,
            passes_defended=self.passes_defended,
            interceptions=self.interceptions,
            defensive_touchdowns=self.defensive_touchdowns,
            field_goals_made=self.field_goals_made,
            field_goals_attempted=self.field_goals_attempted,
            extra_points_made=self.extra_points_made,
            extra_points_attempted=self.extra_points_attempted,
            punts=self.punts,
            kick_returns=self.kick_returns,
            kick_return_touchdowns=self.kick_return_touchdowns,
            punt_returns=self.punt_returns,
            punt_return_touchdowns=self.punt_return_touchdowns,
        )
        for name in ("sacks", "tackles_for_loss"):
            if not (getattr(self, name) * 2).is_integer():
                raise DomainValidationError(f"{name} must be a multiple of 0.5")

    @property
    def yards_per_carry(self) -> float | None:
        if self.rushing_attempts == 0:
            return None
        return self.rushing_yards / self.rushing_attempts

    @property
    def yards_per_reception(self) -> float | None:
        if self.receptions == 0:
            return None
        return self.receiving_yards / self.receptions


@dataclass(frozen=True, slots=True, kw_only=True)
class Absence:
    game_id: UUID
    player_id: UUID
    status: AbsenceStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class PredictionSnapshot:
    id: UUID = field(default_factory=uuid7)
    game_id: UUID
    as_of: datetime
    home_projected_points: float
    away_projected_points: float
    home_win_probability: float
    model_version: str

    def __post_init__(self) -> None:
        _require_timezone_aware("as_of", self.as_of)
        _require_non_negative(
            home_projected_points=self.home_projected_points,
            away_projected_points=self.away_projected_points,
        )
        if not 0.0 <= self.home_win_probability <= 1.0:
            raise DomainValidationError("home_win_probability must be within [0, 1]")

    @property
    def away_win_probability(self) -> float:
        return 1.0 - self.home_win_probability

    @property
    def projected_spread(self) -> float:
        return self.home_projected_points - self.away_projected_points
