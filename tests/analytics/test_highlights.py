from collections.abc import Sequence

import pytest

from tests.analytics.samples import KC, LV
from tests.factories import make_game, make_player
from trench.analytics.highlights import (
    PlayerSeason,
    SeasonLeaders,
    aggregate_seasons,
    season_leaders,
)
from trench.domain.entities import Player, PlayerGameStats
from trench.domain.enums import Position

PASSER = make_player(KC, Position.QB, "Passer")
BACKUP = make_player(LV, Position.QB, "Backup")
WORKHORSE = make_player(KC, Position.RB, "Workhorse")
CAMEO = make_player(LV, Position.RB, "Cameo")
SCRAMBLER = make_player(LV, Position.QB, "Scrambler")
RUSHER = make_player(LV, Position.EDGE, "Rusher")
PLAYERS = {p.id: p for p in (PASSER, BACKUP, WORKHORSE, CAMEO, SCRAMBLER, RUSHER)}
WEEKS = [make_game(KC, LV, week=1), make_game(LV, KC, week=2)]
TEAM_GAMES = {KC.id: 2, LV.id: 2}


def line(
    player: Player,
    week: int,
    *,
    passing_touchdowns: int = 0,
    rushing_attempts: int = 0,
    rushing_yards: int = 0,
    sacks: float = 0.0,
) -> PlayerGameStats:
    return PlayerGameStats(
        game_id=WEEKS[week - 1].id,
        player_id=player.id,
        team_id=player.team_id,
        passing_touchdowns=passing_touchdowns,
        rushing_attempts=rushing_attempts,
        rushing_yards=rushing_yards,
        sacks=sacks,
    )


STATS = [
    line(PASSER, 1, passing_touchdowns=3),
    line(PASSER, 2, passing_touchdowns=2),
    line(BACKUP, 2, passing_touchdowns=1),
    line(WORKHORSE, 1, rushing_attempts=20, rushing_yards=90),
    line(WORKHORSE, 2, rushing_attempts=18, rushing_yards=100),
    line(CAMEO, 2, rushing_attempts=3, rushing_yards=60),
    line(SCRAMBLER, 1, rushing_attempts=15, rushing_yards=120),
    line(RUSHER, 1, sacks=1.5),
    line(RUSHER, 2, sacks=1.0),
]


def leaders(stats: Sequence[PlayerGameStats] = STATS, limit: int = 5) -> SeasonLeaders:
    return season_leaders(
        aggregate_seasons(stats, PLAYERS), team_games=TEAM_GAMES, limit=limit
    )


def names(seasons: Sequence[PlayerSeason]) -> list[str]:
    return [season.player.name for season in seasons]


def test_aggregates_every_game_of_a_player() -> None:
    [workhorse] = [
        s for s in aggregate_seasons(STATS, PLAYERS) if s.player == WORKHORSE
    ]

    assert workhorse.games == 2
    assert workhorse.rushing_attempts == 38
    assert workhorse.yards_per_carry == pytest.approx(190 / 38)


def test_passing_touchdown_leaders() -> None:
    top = leaders().passing_touchdowns

    assert names(top) == ["Passer", "Backup"]
    assert top[0].passing_touchdowns == 5


def test_yards_per_carry_counts_only_qualified_running_backs() -> None:
    assert names(leaders().yards_per_carry) == ["Workhorse"]


def test_sacks_keep_half_sacks() -> None:
    [rusher] = leaders().sacks

    assert rusher.sacks == 2.5


def test_limit_caps_every_category() -> None:
    assert names(leaders(limit=1).passing_touchdowns) == ["Passer"]


def test_ties_favor_fewer_games() -> None:
    tied = [
        line(PASSER, 1, passing_touchdowns=2),
        line(PASSER, 2, passing_touchdowns=0),
        line(BACKUP, 2, passing_touchdowns=2),
    ]

    assert names(leaders(tied).passing_touchdowns) == ["Backup", "Passer"]


def test_no_stats_means_no_leaders() -> None:
    assert leaders([]) == SeasonLeaders(
        passing_touchdowns=(), yards_per_carry=(), sacks=()
    )
