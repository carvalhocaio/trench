import asyncio
import hashlib
from collections import OrderedDict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from trench.analytics.efficiency import TeamEfficiency, compute_efficiency
from trench.analytics.highlights import PlayerSeason, SeasonLeaders
from trench.analytics.ratings import TeamRating
from trench.application.highlights import HighlightsService
from trench.application.lookups import require_team
from trench.application.predictions import GamePrediction, PredictionService
from trench.domain.entities import Team
from trench.domain.enums import Position
from trench.domain.repositories import (
    GameRepository,
    TeamGameStatsRepository,
    TeamRepository,
)


class TeamFacts(BaseModel):
    name: str
    abbreviation: str
    games_played: int
    wins: int
    losses: int
    ties: int
    points_for_avg: float
    points_against_avg: float
    yards_per_play: float | None
    yards_per_play_allowed: float | None
    turnover_margin: float
    projected_points: float
    win_probability_pct: int


class QuarterbackFact(BaseModel):
    player: str
    team: str
    games: int
    passing_yards: int
    passing_touchdowns: int
    interceptions_thrown: int
    rushing_touchdowns: int


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
    quarterbacks: list[QuarterbackFact]

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


class CachingPreviewWriter:
    def __init__(self, writer: PreviewWriter, *, max_entries: int) -> None:
        self._writer = writer
        self._max_entries = max_entries
        self._cache: OrderedDict[str, MatchupPreview] = OrderedDict()
        self._locks: dict[str, asyncio.Lock] = {}
        self._waiters: dict[str, int] = {}

    async def write(self, context: MatchupContext) -> MatchupPreview:
        key = _cache_key(context)
        cached = self._cache.get(key)
        if cached is not None:
            self._cache.move_to_end(key)
            return cached

        lock = self._locks.setdefault(key, asyncio.Lock())
        self._waiters[key] = self._waiters.get(key, 0) + 1
        try:
            async with lock:
                cached = self._cache.get(key)
                if cached is not None:
                    self._cache.move_to_end(key)
                    return cached
                preview = await self._writer.write(context)
                self._cache[key] = preview
                self._cache.move_to_end(key)
                if len(self._cache) > self._max_entries:
                    self._cache.popitem(last=False)
                return preview
        finally:
            self._waiters[key] -= 1
            if self._waiters[key] == 0:
                del self._waiters[key]
                del self._locks[key]


def _cache_key(context: MatchupContext) -> str:
    return hashlib.sha256(context.model_dump_json().encode()).hexdigest()


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
        games: GameRepository,
        team_stats: TeamGameStatsRepository,
        writer: PreviewWriter,
        leaders_limit: int = 10,
    ) -> None:
        self._predictions = predictions
        self._highlights = highlights
        self._teams = teams
        self._games = games
        self._team_stats = team_stats
        self._writer = writer
        self._leaders_limit = leaders_limit

    async def preview(self, game_id: UUID) -> GamePreview:
        prediction = await self._predictions.predict(game_id)
        game = prediction.game
        home = await require_team(self._teams, game.home_team_id)
        away = await require_team(self._teams, game.away_team_id)
        leaders = await self._highlights.season(game.season, limit=self._leaders_limit)
        team_seasons = await self._highlights.for_teams(
            game.season, {game.home_team_id, game.away_team_id}
        )
        efficiency = compute_efficiency(
            await self._games.list_by_season(game.season),
            await self._team_stats.list_by_season(game.season),
        )
        context = build_context(
            prediction,
            home=home,
            away=away,
            leaders=leaders,
            team_seasons=team_seasons,
            efficiency=efficiency,
        )
        return GamePreview(
            prediction=prediction,
            context=context,
            preview=await self._writer.write(context),
        )


def build_context(
    prediction: GamePrediction,
    *,
    home: Team,
    away: Team,
    leaders: SeasonLeaders,
    team_seasons: Iterable[PlayerSeason],
    efficiency: Mapping[UUID, TeamEfficiency],
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
            efficiency.get(home.id),
        ),
        away=_team_facts(
            away,
            prediction.away_rating,
            projection.away_points,
            projection.away_win_probability,
            efficiency.get(away.id),
        ),
        spread=round(projection.spread, 1),
        quarterbacks=_quarterback_facts(team_seasons, teams),
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
    team: Team,
    rating: TeamRating,
    points: float,
    probability: float,
    efficiency: TeamEfficiency | None,
) -> TeamFacts:
    return TeamFacts(
        name=team.name,
        abbreviation=team.abbreviation,
        games_played=rating.games_played,
        wins=rating.wins,
        losses=rating.losses,
        ties=rating.ties,
        points_for_avg=round(rating.points_for_avg, 1),
        points_against_avg=round(rating.points_against_avg, 1),
        yards_per_play=_round_or_none(
            efficiency.yards_per_play if efficiency else None
        ),
        yards_per_play_allowed=_round_or_none(
            efficiency.yards_per_play_allowed if efficiency else None
        ),
        turnover_margin=round(efficiency.turnover_margin, 1) if efficiency else 0.0,
        projected_points=round(points, 1),
        win_probability_pct=round(probability * 100),
    )


def _round_or_none(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None


def _quarterback_facts(
    team_seasons: Iterable[PlayerSeason], teams: dict[UUID, Team]
) -> list[QuarterbackFact]:
    # No starter/depth-chart concept in the domain yet: approximate the
    # starting QB as the one with the most passing yards this season.
    best: dict[UUID, PlayerSeason] = {}
    for season in team_seasons:
        if (
            season.player.position is not Position.QB
            or season.player.team_id not in teams
        ):
            continue
        current = best.get(season.player.team_id)
        if current is None or season.passing_yards > current.passing_yards:
            best[season.player.team_id] = season

    return [
        QuarterbackFact(
            player=season.player.name,
            team=teams[team_id].abbreviation,
            games=season.games,
            passing_yards=season.passing_yards,
            passing_touchdowns=season.passing_touchdowns,
            interceptions_thrown=season.interceptions_thrown,
            rushing_touchdowns=season.rushing_touchdowns,
        )
        for team_id, season in best.items()
    ]


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
