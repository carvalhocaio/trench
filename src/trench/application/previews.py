from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from trench.analytics.highlights import PlayerSeason, SeasonLeaders
from trench.analytics.ratings import TeamRating
from trench.application.highlights import HighlightsService
from trench.application.lookups import require_team
from trench.application.predictions import GamePrediction, PredictionService
from trench.domain.entities import Team
from trench.domain.repositories import TeamRepository


class TeamFacts(BaseModel):
    name: str
    abbreviation: str
    games_played: int
    points_for_avg: float
    points_against_avg: float
    projected_points: float
    win_probability_pct: int


class AbsenceFact(BaseModel):
    player: str
    position: str
    team: str
    status: str
    points_delta: float


class LeaderFact(BaseModel):
    player: str
    team: str
    category: str
    value: float
    games: int


class MatchupContext(BaseModel):
    season: int
    week: int
    kickoff: datetime
    home: TeamFacts
    away: TeamFacts
    spread: float
    absences: list[AbsenceFact]
    leaders: list[LeaderFact]

    @property
    def win_probabilities_pct(self) -> set[int]:
        return {self.home.win_probability_pct, self.away.win_probability_pct}


class MatchupPreview(BaseModel):
    headline: str = Field(max_length=140)
    summary: str
    key_factors: list[str] = Field(min_length=2, max_length=4)
    players_to_watch: list[str] = Field(default_factory=list, max_length=3)


class PreviewWriter(Protocol):
    async def write(self, context: MatchupContext) -> MatchupPreview: ...


class PreviewUnavailableError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class GamePreview:
    prediction: GamePrediction
    context: MatchupContext
    preview: MatchupPreview


class PreviewService:
    def __init__(
        self,
        *,
        predictions: PredictionService,
        highlights: HighlightsService,
        teams: TeamRepository,
        writer: PreviewWriter,
        leaders_limit: int = 10,
    ) -> None:
        self._predictions = predictions
        self._highlights = highlights
        self._teams = teams
        self._writer = writer
        self._leaders_limit = leaders_limit

    async def preview(self, game_id: UUID) -> GamePreview:
        prediction = await self._predictions.predict(game_id)
        game = prediction.game
        home = await require_team(self._teams, game.home_team_id)
        away = await require_team(self._teams, game.away_team_id)
        leaders = await self._highlights.season(game.season, limit=self._leaders_limit)
        context = build_context(prediction, home=home, away=away, leaders=leaders)
        return GamePreview(
            prediction=prediction,
            context=context,
            preview=await self._writer.write(context),
        )


def build_context(
    prediction: GamePrediction, *, home: Team, away: Team, leaders: SeasonLeaders
) -> MatchupContext:
    projection = prediction.projection
    teams = {home.id: home, away.id: away}
    return MatchupContext(
        season=prediction.game.season,
        week=prediction.game.week,
        kickoff=prediction.game.kickoff,
        home=_team_facts(
            home,
            prediction.home_rating,
            projection.home_points,
            projection.home_win_probability,
        ),
        away=_team_facts(
            away,
            prediction.away_rating,
            projection.away_points,
            projection.away_win_probability,
        ),
        spread=round(projection.spread, 1),
        absences=[
            AbsenceFact(
                player=impact.player.name,
                position=impact.player.position,
                team=teams[impact.player.team_id].abbreviation,
                status=impact.status,
                points_delta=round(impact.points_delta, 1),
            )
            for impact in prediction.absences.impacts
        ],
        leaders=[
            *_leader_facts(
                leaders.passing_touchdowns,
                teams,
                category="passing_touchdowns",
                value=lambda s: s.passing_touchdowns,
            ),
            *_leader_facts(
                leaders.yards_per_carry,
                teams,
                category="yards_per_carry",
                value=lambda s: s.yards_per_carry or 0.0,
            ),
            *_leader_facts(
                leaders.sacks, teams, category="sacks", value=lambda s: s.sacks
            ),
        ],
    )


def _team_facts(
    team: Team, rating: TeamRating, points: float, probability: float
) -> TeamFacts:
    return TeamFacts(
        name=team.name,
        abbreviation=team.abbreviation,
        games_played=rating.games_played,
        points_for_avg=round(rating.points_for_avg, 1),
        points_against_avg=round(rating.points_against_avg, 1),
        projected_points=round(points, 1),
        win_probability_pct=round(probability * 100),
    )


def _leader_facts(
    seasons: Iterable[PlayerSeason],
    teams: dict[UUID, Team],
    *,
    category: str,
    value: Callable[[PlayerSeason], float],
) -> list[LeaderFact]:
    return [
        LeaderFact(
            player=season.player.name,
            team=teams[season.player.team_id].abbreviation,
            category=category,
            value=round(value(season), 1),
            games=season.games,
        )
        for season in seasons
        if season.player.team_id in teams
    ]
