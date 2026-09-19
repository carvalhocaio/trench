from uuid import UUID

from trench.application.lookups import (
    require_game,
    require_participant,
    require_player,
)
from trench.domain.entities import Absence
from trench.domain.enums import AbsenceStatus
from trench.domain.repositories import (
    AbsenceRepository,
    GameRepository,
    PlayerRepository,
)


class InjuryReportService:
    def __init__(
        self,
        *,
        games: GameRepository,
        players: PlayerRepository,
        absences: AbsenceRepository,
    ) -> None:
        self._games = games
        self._players = players
        self._absences = absences

    async def report(
        self, game_id: UUID, player_id: UUID, status: AbsenceStatus
    ) -> Absence:
        game = await require_game(self._games, game_id)
        player = await require_player(self._players, player_id)
        require_participant(game, player.team_id)
        absence = Absence(game_id=game.id, player_id=player.id, status=status)
        await self._absences.save(absence)
        return absence

    async def clear(self, game_id: UUID, player_id: UUID) -> None:
        await require_game(self._games, game_id)
        await self._absences.remove(game_id, player_id)

    async def list_game(self, game_id: UUID) -> list[Absence]:
        await require_game(self._games, game_id)
        return await self._absences.list_by_game(game_id)
