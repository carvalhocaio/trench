from uuid import UUID

from trench.application.errors import (
    GameNotFoundError,
    PlayerNotFoundError,
    TeamNotFoundError,
    TeamNotInGameError,
)
from trench.domain.entities import Game, Player, Team
from trench.domain.repositories import GameRepository, PlayerRepository, TeamRepository


async def require_team(teams: TeamRepository, team_id: UUID) -> Team:
    team = await teams.get(team_id)
    if team is None:
        raise TeamNotFoundError(team_id)
    return team


async def require_game(games: GameRepository, game_id: UUID) -> Game:
    game = await games.get(game_id)
    if game is None:
        raise GameNotFoundError(game_id)
    return game


async def require_player(players: PlayerRepository, player_id: UUID) -> Player:
    player = await players.get(player_id)
    if player is None:
        raise PlayerNotFoundError(player_id)
    return player


def require_participant(game: Game, team_id: UUID) -> None:
    if not game.involves(team_id):
        raise TeamNotInGameError(team_id, game.id)
