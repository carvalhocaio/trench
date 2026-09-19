from datetime import timedelta
from uuid import uuid7

import pytest

from tests.analytics.samples import DEN, KC, LAC, LV
from tests.factories import SEASON_OPENER, make_team
from tests.fakes import FakeGameRepository, FakeTeamRepository
from trench.application.errors import (
    GameNotFoundError,
    ScheduleConflictError,
    TeamNotFoundError,
)
from trench.application.schedule import ScheduleService
from trench.domain.entities import Game, Score, Team
from trench.domain.enums import GameStatus
from trench.domain.errors import DomainValidationError, GameNotStartedError

AFTER_KICKOFF = SEASON_OPENER + timedelta(hours=3)


@pytest.fixture
async def schedule() -> ScheduleService:
    teams = FakeTeamRepository()
    for team in (KC, LV, DEN, LAC):
        await teams.save(team)
    return ScheduleService(
        teams=teams, games=FakeGameRepository(), clock=lambda: AFTER_KICKOFF
    )


async def book(
    schedule: ScheduleService, home: Team, away: Team, *, week: int = 1
) -> Game:
    return await schedule.schedule(
        season=2026,
        week=week,
        kickoff=SEASON_OPENER,
        home_team_id=home.id,
        away_team_id=away.id,
    )


async def test_schedules_game(schedule: ScheduleService) -> None:
    game = await book(schedule, KC, LV)

    assert await schedule.get(game.id) == game
    assert game.status is GameStatus.SCHEDULED


@pytest.mark.parametrize(("home", "away"), [(KC, DEN), (DEN, KC), (LAC, KC)])
async def test_team_cannot_play_twice_in_a_week(
    schedule: ScheduleService, home: Team, away: Team
) -> None:
    await book(schedule, KC, LV)

    with pytest.raises(ScheduleConflictError):
        await book(schedule, home, away)


async def test_same_teams_can_meet_again_in_another_week(
    schedule: ScheduleService,
) -> None:
    await book(schedule, KC, LV, week=1)

    rematch = await book(schedule, LV, KC, week=11)

    assert rematch.week == 11


async def test_rejects_unknown_team(schedule: ScheduleService) -> None:
    with pytest.raises(TeamNotFoundError):
        await book(schedule, KC, make_team("XX"))


async def test_domain_rules_apply_before_lookups(schedule: ScheduleService) -> None:
    with pytest.raises(DomainValidationError):
        await book(schedule, KC, KC)


async def test_records_and_corrects_score(schedule: ScheduleService) -> None:
    game = await book(schedule, KC, LV)

    await schedule.record_score(game.id, Score(home=24, away=21))
    corrected = await schedule.record_score(game.id, Score(home=27, away=21))

    assert corrected.score == Score(home=27, away=21)
    assert (await schedule.get(game.id)).score == Score(home=27, away=21)


async def test_record_score_of_unknown_game(schedule: ScheduleService) -> None:
    with pytest.raises(GameNotFoundError):
        await schedule.record_score(uuid7(), Score(home=1, away=0))


async def test_record_score_before_kickoff_is_rejected() -> None:
    teams = FakeTeamRepository()
    for team in (KC, LV):
        await teams.save(team)
    early_schedule = ScheduleService(
        teams=teams,
        games=FakeGameRepository(),
        clock=lambda: SEASON_OPENER - timedelta(hours=1),
    )
    game = await book(early_schedule, KC, LV)

    with pytest.raises(GameNotStartedError):
        await early_schedule.record_score(game.id, Score(home=1, away=0))


async def test_find_by_week_and_team(schedule: ScheduleService) -> None:
    week_one = await book(schedule, KC, LV, week=1)
    other = await book(schedule, DEN, LAC, week=1)
    week_two = await book(schedule, DEN, KC, week=2)

    assert await schedule.find(2026, week=1) == [week_one, other]
    assert await schedule.find(2026, team_id=KC.id) == [week_one, week_two]
    assert await schedule.find(2026, week=2, team_id=KC.id) == [week_two]


async def test_find_by_unknown_team(schedule: ScheduleService) -> None:
    with pytest.raises(TeamNotFoundError):
        await schedule.find(2026, team_id=uuid7())
