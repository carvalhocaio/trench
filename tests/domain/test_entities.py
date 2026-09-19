from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid7

import pytest

from trench.domain.entities import (
    Game,
    PlayerGameStats,
    PredictionSnapshot,
    Score,
    TeamGameStats,
)
from trench.domain.enums import GameStatus
from trench.domain.errors import DomainValidationError, GameNotStartedError

KICKOFF = datetime(2026, 9, 20, 17, 0, tzinfo=UTC)


def make_game(**overrides: Any) -> Game:
    base = Game(
        season=2026,
        week=2,
        kickoff=KICKOFF,
        home_team_id=uuid7(),
        away_team_id=uuid7(),
    )
    return replace(base, **overrides)


class TestGame:
    def test_scheduled_until_finalized(self) -> None:
        game = make_game()

        final = game.finalize(Score(home=27, away=20), at=game.kickoff)

        assert game.status is GameStatus.SCHEDULED
        assert final.status is GameStatus.FINAL

    def test_finalize_rejects_before_kickoff(self) -> None:
        game = make_game()

        with pytest.raises(GameNotStartedError):
            game.finalize(
                Score(home=27, away=20), at=game.kickoff - timedelta(seconds=1)
            )

    def test_finalize_allows_at_kickoff(self) -> None:
        game = make_game()

        final = game.finalize(Score(home=27, away=20), at=game.kickoff)

        assert final.status is GameStatus.FINAL

    def test_finalize_allows_after_kickoff(self) -> None:
        game = make_game()

        final = game.finalize(
            Score(home=27, away=20), at=game.kickoff + timedelta(hours=3)
        )

        assert final.status is GameStatus.FINAL

    def test_points_from_each_side(self) -> None:
        game = make_game(score=Score(home=31, away=17))

        assert game.points_for(game.home_team_id) == 31
        assert game.points_against(game.home_team_id) == 17
        assert game.points_for(game.away_team_id) == 17
        assert game.winner_id() == game.home_team_id

    def test_tie_has_no_winner(self) -> None:
        game = make_game(score=Score(home=20, away=20))

        assert game.winner_id() is None

    def test_points_require_final_score(self) -> None:
        game = make_game()

        with pytest.raises(DomainValidationError, match="no final score"):
            game.points_for(game.home_team_id)

    def test_rejects_outsider_team(self) -> None:
        game = make_game(score=Score(home=10, away=3))

        with pytest.raises(DomainValidationError, match="not part of game"):
            game.opponent_of(uuid7())

    @pytest.mark.parametrize(
        "overrides",
        [
            {"week": 0},
            {"week": 19},
            {"kickoff": datetime(2026, 9, 20, 17, 0)},
        ],
    )
    def test_rejects_invalid_state(self, overrides: dict[str, object]) -> None:
        with pytest.raises(DomainValidationError):
            make_game(**overrides)

    def test_rejects_same_team_on_both_sides(self) -> None:
        team_id = uuid7()

        with pytest.raises(DomainValidationError, match="against itself"):
            make_game(home_team_id=team_id, away_team_id=team_id)


def test_score_rejects_negative_points() -> None:
    with pytest.raises(DomainValidationError, match="home"):
        Score(home=-3, away=7)


class TestTeamGameStats:
    def test_yards_per_play(self) -> None:
        stats = TeamGameStats(
            game_id=uuid7(),
            team_id=uuid7(),
            offensive_plays=60,
            passing_yards=250,
            rushing_yards=110,
            turnovers=1,
            sacks=3,
        )

        assert stats.total_yards == 360
        assert stats.yards_per_play == pytest.approx(6.0)

    def test_allows_negative_net_yards(self) -> None:
        stats = TeamGameStats(
            game_id=uuid7(),
            team_id=uuid7(),
            offensive_plays=45,
            passing_yards=-4,
            rushing_yards=80,
            turnovers=3,
            sacks=0,
        )

        assert stats.total_yards == 76


class TestPlayerGameStats:
    def test_yards_per_carry(self) -> None:
        stats = PlayerGameStats(
            game_id=uuid7(),
            player_id=uuid7(),
            team_id=uuid7(),
            rushing_attempts=20,
            rushing_yards=94,
        )

        assert stats.yards_per_carry == pytest.approx(4.7)

    def test_yards_per_carry_without_attempts(self) -> None:
        stats = PlayerGameStats(game_id=uuid7(), player_id=uuid7(), team_id=uuid7())

        assert stats.yards_per_carry is None

    def test_accepts_half_sacks(self) -> None:
        stats = PlayerGameStats(
            game_id=uuid7(), player_id=uuid7(), team_id=uuid7(), sacks=1.5
        )

        assert stats.sacks == 1.5

    def test_rejects_fractional_sacks(self) -> None:
        with pytest.raises(DomainValidationError, match="multiple of"):
            PlayerGameStats(
                game_id=uuid7(), player_id=uuid7(), team_id=uuid7(), sacks=0.3
            )

    def test_yards_per_reception(self) -> None:
        stats = PlayerGameStats(
            game_id=uuid7(),
            player_id=uuid7(),
            team_id=uuid7(),
            receptions=5,
            receiving_yards=60,
        )

        assert stats.yards_per_reception == pytest.approx(12.0)

    def test_yards_per_reception_without_receptions(self) -> None:
        stats = PlayerGameStats(game_id=uuid7(), player_id=uuid7(), team_id=uuid7())

        assert stats.yards_per_reception is None

    def test_accepts_half_tackles_for_loss(self) -> None:
        stats = PlayerGameStats(
            game_id=uuid7(), player_id=uuid7(), team_id=uuid7(), tackles_for_loss=1.5
        )

        assert stats.tackles_for_loss == 1.5

    def test_rejects_fractional_tackles_for_loss(self) -> None:
        with pytest.raises(DomainValidationError, match="multiple of"):
            PlayerGameStats(
                game_id=uuid7(),
                player_id=uuid7(),
                team_id=uuid7(),
                tackles_for_loss=0.3,
            )

    def test_rejects_negative_new_stat_fields(self) -> None:
        with pytest.raises(DomainValidationError, match="non-negative"):
            PlayerGameStats(
                game_id=uuid7(), player_id=uuid7(), team_id=uuid7(), tackles=-1
            )


class TestPredictionSnapshot:
    def test_complementary_probability_and_spread(self) -> None:
        snapshot = PredictionSnapshot(
            game_id=uuid7(),
            as_of=KICKOFF,
            home_projected_points=24.5,
            away_projected_points=20.0,
            home_win_probability=0.63,
            model_version="0.1.0",
        )

        assert snapshot.away_win_probability == pytest.approx(0.37)
        assert snapshot.projected_spread == pytest.approx(4.5)

    def test_rejects_probability_out_of_range(self) -> None:
        with pytest.raises(DomainValidationError, match=r"\[0, 1\]"):
            PredictionSnapshot(
                game_id=uuid7(),
                as_of=KICKOFF,
                home_projected_points=24.5,
                away_projected_points=20.0,
                home_win_probability=1.2,
                model_version="0.1.0",
            )
