from collections.abc import Iterable
from dataclasses import dataclass

from trench.domain.entities import Game
from trench.domain.enums import GameStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class HomeFieldEffect:
    games: int
    home_win_rate: float | None
    average_home_margin: float | None


def compute_home_field_effect(games: Iterable[Game]) -> HomeFieldEffect:
    final_games = [game for game in games if game.status is GameStatus.FINAL]
    decided_games = [game for game in final_games if game.winner_id() is not None]
    home_wins = sum(
        1 for game in decided_games if game.winner_id() == game.home_team_id
    )
    margins = [
        game.points_for(game.home_team_id) - game.points_against(game.home_team_id)
        for game in final_games
    ]
    return HomeFieldEffect(
        games=len(final_games),
        home_win_rate=home_wins / len(decided_games) if decided_games else None,
        average_home_margin=sum(margins) / len(margins) if margins else None,
    )
