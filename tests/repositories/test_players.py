from dataclasses import replace

from tests.factories import make_player
from tests.repositories.conftest import AfcWest, Repositories
from trench.domain.enums import Position


async def test_save_and_get(repos: Repositories, afc_west: AfcWest) -> None:
    player = make_player(afc_west.kc, Position.QB, "Quarterback One")

    await repos.players.save(player)

    assert await repos.players.get(player.id) == player


async def test_list_by_team_orders_by_position_and_name(
    repos: Repositories, afc_west: AfcWest
) -> None:
    rusher = make_player(afc_west.kc, Position.RB, "Runner")
    passer = make_player(afc_west.kc, Position.QB, "Passer")
    backup = make_player(afc_west.kc, Position.QB, "Backup")
    rival = make_player(afc_west.lv, Position.QB, "Rival")
    for player in (rusher, passer, backup, rival):
        await repos.players.save(player)

    assert await repos.players.list_by_team(afc_west.kc.id) == [
        backup,
        passer,
        rusher,
    ]


async def test_save_moves_traded_player(repos: Repositories, afc_west: AfcWest) -> None:
    player = make_player(afc_west.kc, Position.EDGE, "Pass Rusher")
    await repos.players.save(player)

    await repos.players.save(replace(player, team_id=afc_west.den.id))

    assert await repos.players.list_by_team(afc_west.kc.id) == []
    assert await repos.players.list_by_team(afc_west.den.id) == [
        replace(player, team_id=afc_west.den.id)
    ]
