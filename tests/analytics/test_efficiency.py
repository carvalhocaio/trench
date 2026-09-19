import pytest

from tests.analytics.samples import DEN, KC, LAC, LV, WEEK_ONE
from tests.factories import make_game
from trench.analytics.efficiency import compute_efficiency, pair_with_opponent
from trench.domain.entities import TeamGameStats

KC_STATS = TeamGameStats(
    game_id=WEEK_ONE[0].id,
    team_id=KC.id,
    offensive_plays=60,
    passing_yards=200,
    rushing_yards=160,
    turnovers=0,
    sacks=1,
)
LV_STATS = TeamGameStats(
    game_id=WEEK_ONE[0].id,
    team_id=LV.id,
    offensive_plays=60,
    passing_yards=100,
    rushing_yards=80,
    turnovers=2,
    sacks=4,
)


def test_pair_with_opponent_matches_both_sides_of_a_final_game() -> None:
    pairs = pair_with_opponent(WEEK_ONE, [KC_STATS, LV_STATS])

    assert pairs[KC.id] == [(KC_STATS, LV_STATS)]
    assert pairs[LV.id] == [(LV_STATS, KC_STATS)]


def test_pair_with_opponent_ignores_games_missing_one_sides_stats() -> None:
    pairs = pair_with_opponent(WEEK_ONE, [KC_STATS])

    assert KC.id not in pairs
    assert LV.id not in pairs


def test_pair_with_opponent_ignores_unfinished_games() -> None:
    upcoming = make_game(DEN, LAC, week=3)
    stats = TeamGameStats(
        game_id=upcoming.id,
        team_id=DEN.id,
        offensive_plays=60,
        passing_yards=200,
        rushing_yards=160,
        turnovers=0,
        sacks=1,
    )

    pairs = pair_with_opponent([*WEEK_ONE, upcoming], [KC_STATS, LV_STATS, stats])

    assert DEN.id not in pairs


def test_compute_efficiency_derives_offense_and_defense_from_the_matchup() -> None:
    efficiency = compute_efficiency(WEEK_ONE, [KC_STATS, LV_STATS])

    kc = efficiency[KC.id]
    assert kc.games_played == 1
    assert kc.yards_per_play == pytest.approx(6.0)
    assert kc.yards_per_play_allowed == pytest.approx(3.0)
    assert kc.turnover_margin == pytest.approx(2.0)
    assert kc.sacks_made_per_game == pytest.approx(4.0)
    assert kc.sacks_allowed_per_game == pytest.approx(1.0)

    lv = efficiency[LV.id]
    assert lv.yards_per_play == pytest.approx(3.0)
    assert lv.yards_per_play_allowed == pytest.approx(6.0)
    assert lv.turnover_margin == pytest.approx(-2.0)
    assert lv.sacks_made_per_game == pytest.approx(1.0)
    assert lv.sacks_allowed_per_game == pytest.approx(4.0)


def test_compute_efficiency_skips_teams_without_any_stats() -> None:
    efficiency = compute_efficiency(WEEK_ONE, [KC_STATS, LV_STATS])

    assert DEN.id not in efficiency
    assert LAC.id not in efficiency
