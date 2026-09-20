import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid7

import pytest

from tests.agent.samples import CONTEXT, GROUNDED
from tests.analytics.samples import DEN, KC, LAC, LV, WEEK_ONE, final
from tests.factories import make_game, make_player
from tests.fakes import (
    FakeAbsenceRepository,
    FakeGameRepository,
    FakePlayerGameStatsRepository,
    FakePlayerRepository,
    FakePredictionSnapshotRepository,
    FakeTeamGameStatsRepository,
    FakeTeamRepository,
)
from trench.analytics.absences import AbsenceReport
from trench.analytics.highlights import SeasonLeaders
from trench.analytics.projection import Projection
from trench.analytics.ratings import TeamRating
from trench.application.highlights import HighlightsService
from trench.application.predictions import GamePrediction, PredictionService
from trench.application.previews import (
    CachingPreviewWriter,
    GameOutcomeFact,
    MatchupContext,
    MatchupPreview,
    PreviewService,
    PreviewUnavailableError,
    build_context,
)
from trench.config import AnalyticsSettings
from trench.domain.entities import Absence, Game, PlayerGameStats, TeamGameStats
from trench.domain.enums import AbsenceStatus, Position


class RecordingWriter:
    def __init__(self) -> None:
        self.contexts: list[MatchupContext] = []

    async def write(self, context: MatchupContext) -> MatchupPreview:
        self.contexts.append(context)
        return GROUNDED


@dataclass(frozen=True)
class Setup:
    service: PreviewService
    writer: RecordingWriter
    game_id: UUID


@pytest.fixture
async def setup() -> Setup:
    teams = FakeTeamRepository()
    games = FakeGameRepository()
    players = FakePlayerRepository()
    absences = FakeAbsenceRepository()
    player_stats = FakePlayerGameStatsRepository(games)
    team_stats = FakeTeamGameStatsRepository(games)
    for team in (KC, LV, DEN, LAC):
        await teams.save(team)
    for game in WEEK_ONE:
        await games.save(game)
    rematch = make_game(LV, KC, week=2)
    await games.save(rematch)

    quarterback = make_player(LV, Position.QB, "Raider Passer")
    passer = make_player(KC, Position.QB, "Chief Passer")
    outsider = make_player(DEN, Position.QB, "Bronco Passer")
    for player in (quarterback, passer, outsider):
        await players.save(player)
    await absences.save(
        Absence(game_id=rematch.id, player_id=quarterback.id, status=AbsenceStatus.OUT)
    )
    for player, game in ((passer, WEEK_ONE[0]), (outsider, WEEK_ONE[1])):
        await player_stats.save(
            PlayerGameStats(
                game_id=game.id,
                player_id=player.id,
                team_id=player.team_id,
                passing_touchdowns=3,
            )
        )
    await team_stats.save(
        TeamGameStats(
            game_id=WEEK_ONE[0].id,
            team_id=KC.id,
            offensive_plays=60,
            passing_yards=250,
            rushing_yards=110,
            turnovers=0,
            sacks=1,
        )
    )
    await team_stats.save(
        TeamGameStats(
            game_id=WEEK_ONE[0].id,
            team_id=LV.id,
            offensive_plays=65,
            passing_yards=150,
            rushing_yards=60,
            turnovers=2,
            sacks=3,
        )
    )

    writer = RecordingWriter()
    settings = AnalyticsSettings(_env_file=None)  # pyright: ignore[reportCallIssue]
    service = PreviewService(
        predictions=PredictionService(
            games=games,
            players=players,
            absences=absences,
            snapshots=FakePredictionSnapshotRepository(games),
            team_stats=team_stats,
            settings=settings,
            clock=lambda: datetime(2026, 9, 16, tzinfo=UTC),
        ),
        highlights=HighlightsService(
            games=games, players=players, player_stats=player_stats
        ),
        teams=teams,
        games=games,
        team_stats=team_stats,
        writer=writer,
    )
    return Setup(service=service, writer=writer, game_id=rematch.id)


async def test_preview_combines_prediction_and_narrative(
    setup: Setup,
) -> None:
    preview = await setup.service.preview(setup.game_id)

    assert preview.preview == GROUNDED
    assert preview.prediction.game.id == setup.game_id


async def test_context_is_grounded_in_the_prediction(
    setup: Setup,
) -> None:
    preview = await setup.service.preview(setup.game_id)

    [context] = setup.writer.contexts
    projection = preview.prediction.projection
    assert context.home.abbreviation == "LV"
    assert context.away.name == KC.name
    assert context.home.win_probability_pct == round(
        projection.home_win_probability * 100
    )
    [absence] = context.absences
    assert (absence.player, absence.team, absence.status) == (
        "Raider Passer",
        "LV",
        "OUT",
    )


async def test_context_only_lists_leaders_from_both_teams(
    setup: Setup,
) -> None:
    await setup.service.preview(setup.game_id)

    [context] = setup.writer.contexts
    assert [(leader.player, leader.team) for leader in context.leaders] == [
        ("Chief Passer", "KC")
    ]


async def test_context_includes_team_efficiency_and_quarterbacks(
    setup: Setup,
) -> None:
    await setup.service.preview(setup.game_id)

    [context] = setup.writer.contexts
    assert context.away.abbreviation == "KC"
    assert context.away.yards_per_play == pytest.approx(6.0)
    assert context.away.yards_per_play_allowed == pytest.approx(round(210 / 65, 1))
    assert context.away.turnover_margin == pytest.approx(2.0)
    assert context.home.abbreviation == "LV"
    assert context.home.yards_per_play == pytest.approx(round(210 / 65, 1))
    assert context.home.yards_per_play_allowed == pytest.approx(6.0)
    assert context.home.turnover_margin == pytest.approx(-2.0)
    assert [(qb.player, qb.team) for qb in context.quarterbacks] == [
        ("Chief Passer", "KC")
    ]


class CountingWriter:
    def __init__(self, *, fail_first: int = 0, delay: float = 0.0) -> None:
        self.calls = 0
        self._fail_first = fail_first
        self._delay = delay

    async def write(self, context: MatchupContext) -> MatchupPreview:
        self.calls += 1
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._fail_first > 0:
            self._fail_first -= 1
            raise PreviewUnavailableError("boom")
        return GROUNDED


async def test_same_context_writes_once() -> None:
    writer = CountingWriter()
    cache = CachingPreviewWriter(writer, max_entries=10)

    first = await cache.write(CONTEXT)
    second = await cache.write(CONTEXT)

    assert first == second == GROUNDED
    assert writer.calls == 1


async def test_different_context_writes_again() -> None:
    writer = CountingWriter()
    cache = CachingPreviewWriter(writer, max_entries=10)
    other = CONTEXT.model_copy(update={"spread": CONTEXT.spread - 1})

    await cache.write(CONTEXT)
    await cache.write(other)

    assert writer.calls == 2


async def test_oldest_entry_is_evicted_past_the_limit() -> None:
    writer = CountingWriter()
    cache = CachingPreviewWriter(writer, max_entries=2)
    first = CONTEXT.model_copy(update={"spread": 1.0})
    second = CONTEXT.model_copy(update={"spread": 2.0})
    third = CONTEXT.model_copy(update={"spread": 3.0})

    await cache.write(first)
    await cache.write(second)
    await cache.write(third)
    await cache.write(first)

    assert writer.calls == 4


async def test_failure_is_not_cached() -> None:
    writer = CountingWriter(fail_first=1)
    cache = CachingPreviewWriter(writer, max_entries=10)

    with pytest.raises(PreviewUnavailableError):
        await cache.write(CONTEXT)
    result = await cache.write(CONTEXT)

    assert result == GROUNDED
    assert writer.calls == 2


async def test_concurrent_calls_write_once() -> None:
    writer = CountingWriter(delay=0.01)
    cache = CachingPreviewWriter(writer, max_entries=10)

    results = await asyncio.gather(*(cache.write(CONTEXT) for _ in range(5)))

    assert all(result == GROUNDED for result in results)
    assert writer.calls == 1


EMPTY_LEADERS = SeasonLeaders(
    passing_yards=(),
    passing_touchdowns=(),
    rushing_touchdowns_qb=(),
    yards_per_carry=(),
    sacks=(),
    interceptions=(),
)


def _neutral_rating() -> TeamRating:
    return TeamRating(
        team_id=uuid7(),
        games_played=1,
        wins=1,
        losses=0,
        ties=0,
        points_for_avg=20.0,
        points_against_avg=20.0,
        offense_strength=1.0,
        defense_strength=1.0,
    )


def _prediction(game: Game, *, home_win_probability: float) -> GamePrediction:
    return GamePrediction(
        game=game,
        home_rating=_neutral_rating(),
        away_rating=_neutral_rating(),
        absences=AbsenceReport(impacts=()),
        projection=Projection(
            home_points=24.0,
            away_points=20.0,
            home_win_probability=home_win_probability,
        ),
        as_of=datetime(2026, 9, 16, tzinfo=UTC),
    )


def test_outcome_is_none_before_the_game_is_played() -> None:
    prediction = _prediction(make_game(KC, LV, week=2), home_win_probability=0.8)

    context = build_context(
        prediction,
        home=KC,
        away=LV,
        leaders=EMPTY_LEADERS,
        team_seasons=[],
        efficiency={},
    )

    assert context.outcome is None


def test_outcome_marks_the_favorite_winning_as_not_an_upset() -> None:
    game = final(KC, LV, (30, 10), week=2)
    prediction = _prediction(game, home_win_probability=0.8)

    context = build_context(
        prediction,
        home=KC,
        away=LV,
        leaders=EMPTY_LEADERS,
        team_seasons=[],
        efficiency={},
    )

    assert context.outcome == GameOutcomeFact(
        home_score=30, away_score=10, winner="KC", was_upset=False
    )


def test_outcome_flags_an_upset_when_the_underdog_wins() -> None:
    game = final(KC, LV, (10, 30), week=2)
    prediction = _prediction(game, home_win_probability=0.8)

    context = build_context(
        prediction,
        home=KC,
        away=LV,
        leaders=EMPTY_LEADERS,
        team_seasons=[],
        efficiency={},
    )

    assert context.outcome == GameOutcomeFact(
        home_score=10, away_score=30, winner="LV", was_upset=True
    )


def test_outcome_handles_ties_without_an_upset() -> None:
    game = final(KC, LV, (20, 20), week=2)
    prediction = _prediction(game, home_win_probability=0.5)

    context = build_context(
        prediction,
        home=KC,
        away=LV,
        leaders=EMPTY_LEADERS,
        team_seasons=[],
        efficiency={},
    )

    assert context.outcome == GameOutcomeFact(
        home_score=20, away_score=20, winner=None, was_upset=False
    )
