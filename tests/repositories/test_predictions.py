from datetime import timedelta

from tests.factories import SEASON
from tests.repositories.conftest import Repositories
from trench.domain.entities import Game, PredictionSnapshot


def snapshot(game: Game, *, days_before: int, probability: float) -> PredictionSnapshot:
    return PredictionSnapshot(
        game_id=game.id,
        as_of=game.kickoff - timedelta(days=days_before),
        home_projected_points=24.0,
        away_projected_points=21.0,
        home_win_probability=probability,
        model_version="0.1.0",
    )


async def test_snapshots_are_appended_in_chronological_order(
    repos: Repositories, game: Game
) -> None:
    saturday = snapshot(game, days_before=1, probability=0.58)
    wednesday = snapshot(game, days_before=4, probability=0.61)
    for item in (saturday, wednesday):
        await repos.predictions.save(item)

    assert await repos.predictions.list_by_game(game.id) == [wednesday, saturday]
    assert await repos.predictions.list_by_season(SEASON) == [wednesday, saturday]
    assert await repos.predictions.list_by_season(SEASON - 1) == []
