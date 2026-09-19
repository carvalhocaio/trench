from uuid import uuid7

import pytest

from tests.analytics.samples import KC, LV, WEEK_ONE
from tests.factories import make_game, make_player
from trench.analytics.absences import (
    NO_ADJUSTMENT,
    PointsAdjustment,
    assess_absences,
)
from trench.analytics.projection import project_game
from trench.analytics.ratings import compute_ratings
from trench.config import DEFAULT_ABSENCE_PROBABILITIES, DEFAULT_POSITION_WEIGHTS
from trench.domain.entities import Absence, Game, Player
from trench.domain.enums import AbsenceStatus, Position

GAME = make_game(KC, LV, week=2)
KC_QB = make_player(KC, Position.QB, "Home Quarterback")
KC_CB = make_player(KC, Position.CB, "Home Corner")
LV_WR = make_player(LV, Position.WR, "Away Receiver")
LV_EDGE = make_player(LV, Position.EDGE, "Away Edge")
PLAYERS = {player.id: player for player in (KC_QB, KC_CB, LV_WR, LV_EDGE)}


def absence(player: Player, status: AbsenceStatus, game: Game = GAME) -> Absence:
    return Absence(game_id=game.id, player_id=player.id, status=status)


def assess(*absences: Absence) -> PointsAdjustment:
    return assess_absences(
        GAME,
        absences,
        PLAYERS,
        position_weights=DEFAULT_POSITION_WEIGHTS,
        absence_probabilities=DEFAULT_ABSENCE_PROBABILITIES,
    ).adjustment


def test_offensive_absence_lowers_own_points() -> None:
    adjustment = assess(absence(KC_QB, AbsenceStatus.OUT))

    assert adjustment == PointsAdjustment(home=-DEFAULT_POSITION_WEIGHTS[Position.QB])


def test_defensive_absence_raises_opponent_points() -> None:
    adjustment = assess(absence(KC_CB, AbsenceStatus.OUT))

    assert adjustment == PointsAdjustment(away=DEFAULT_POSITION_WEIGHTS[Position.CB])


def test_away_team_absences_mirror_home_rules() -> None:
    adjustment = assess(
        absence(LV_WR, AbsenceStatus.OUT), absence(LV_EDGE, AbsenceStatus.OUT)
    )

    assert adjustment.away == pytest.approx(-DEFAULT_POSITION_WEIGHTS[Position.WR])
    assert adjustment.home == pytest.approx(DEFAULT_POSITION_WEIGHTS[Position.EDGE])


def test_status_scales_impact_by_absence_probability() -> None:
    adjustment = assess(absence(KC_QB, AbsenceStatus.QUESTIONABLE))

    assert adjustment.home == pytest.approx(
        -DEFAULT_POSITION_WEIGHTS[Position.QB]
        * DEFAULT_ABSENCE_PROBABILITIES[AbsenceStatus.QUESTIONABLE]
    )


def test_impacts_are_ranked_by_magnitude() -> None:
    report = assess_absences(
        GAME,
        [absence(LV_WR, AbsenceStatus.OUT), absence(KC_QB, AbsenceStatus.OUT)],
        PLAYERS,
        position_weights=DEFAULT_POSITION_WEIGHTS,
        absence_probabilities=DEFAULT_ABSENCE_PROBABILITIES,
    )

    assert [impact.player for impact in report.impacts] == [KC_QB, LV_WR]


def test_no_absences_means_no_adjustment() -> None:
    assert assess() == NO_ADJUSTMENT


def test_rejects_absence_from_another_game() -> None:
    other_game = make_game(LV, KC, week=3)

    with pytest.raises(ValueError, match="belongs to game"):
        assess(absence(KC_QB, AbsenceStatus.OUT, other_game))


def test_rejects_unknown_player() -> None:
    stranger = Absence(game_id=GAME.id, player_id=uuid7(), status=AbsenceStatus.OUT)

    with pytest.raises(ValueError, match="unknown player"):
        assess(stranger)


def test_missing_quarterback_shifts_win_probability() -> None:
    ratings = compute_ratings(WEEK_ONE, shrinkage_games=3.0)

    def home_probability(adjustment: PointsAdjustment) -> float:
        return project_game(
            ratings,
            home_team_id=KC.id,
            away_team_id=LV.id,
            home_field_advantage=1.7,
            score_margin_stddev=13.5,
            adjustment=adjustment,
        ).home_win_probability

    healthy = home_probability(NO_ADJUSTMENT)
    without_qb = home_probability(assess(absence(KC_QB, AbsenceStatus.OUT)))

    assert without_qb < healthy
