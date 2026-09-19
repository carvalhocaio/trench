from tests.factories import make_player
from tests.repositories.conftest import AfcWest, Repositories
from trench.domain.entities import Absence, Game
from trench.domain.enums import AbsenceStatus, Position


async def test_status_changes_along_the_week(
    repos: Repositories, afc_west: AfcWest, game: Game
) -> None:
    player = make_player(afc_west.kc, Position.WR, "Receiver")
    await repos.players.save(player)
    questionable = Absence(
        game_id=game.id, player_id=player.id, status=AbsenceStatus.QUESTIONABLE
    )
    out = Absence(game_id=game.id, player_id=player.id, status=AbsenceStatus.OUT)

    await repos.absences.save(questionable)
    await repos.absences.save(out)

    assert await repos.absences.list_by_game(game.id) == [out]


async def test_remove_clears_player_from_report(
    repos: Repositories, afc_west: AfcWest, game: Game
) -> None:
    player = make_player(afc_west.lv, Position.CB, "Corner")
    await repos.players.save(player)
    await repos.absences.save(
        Absence(game_id=game.id, player_id=player.id, status=AbsenceStatus.DOUBTFUL)
    )

    await repos.absences.remove(game.id, player.id)

    assert await repos.absences.list_by_game(game.id) == []
