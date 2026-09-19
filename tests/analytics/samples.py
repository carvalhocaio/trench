from tests.factories import make_game, make_team
from trench.domain.entities import Game, Score, Team

KC, LV, DEN, LAC = (make_team(code) for code in ("KC", "LV", "DEN", "LAC"))


def final(home: Team, away: Team, points: tuple[int, int], *, week: int) -> Game:
    home_points, away_points = points
    game = make_game(home, away, week=week)
    return game.finalize(Score(home=home_points, away=away_points), at=game.kickoff)


WEEK_ONE = [final(KC, LV, (30, 10), week=1), final(DEN, LAC, (20, 20), week=1)]
