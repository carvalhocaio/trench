from uuid import UUID

from trench.application.lookups import require_player, require_team
from trench.domain.entities import Player
from trench.domain.enums import Position
from trench.domain.repositories import PlayerRepository, TeamRepository


class RosterService:
    def __init__(self, *, teams: TeamRepository, players: PlayerRepository) -> None:
        self._teams = teams
        self._players = players

    async def register(self, *, name: str, team_id: UUID, position: Position) -> Player:
        await require_team(self._teams, team_id)
        player = Player(name=name, team_id=team_id, position=position)
        await self._players.save(player)
        return player

    async def update(
        self, player_id: UUID, *, name: str, team_id: UUID, position: Position
    ) -> Player:
        await require_player(self._players, player_id)
        await require_team(self._teams, team_id)
        player = Player(id=player_id, name=name, team_id=team_id, position=position)
        await self._players.save(player)
        return player

    async def get(self, player_id: UUID) -> Player:
        return await require_player(self._players, player_id)

    async def list_team(self, team_id: UUID) -> list[Player]:
        await require_team(self._teams, team_id)
        return await self._players.list_by_team(team_id)
