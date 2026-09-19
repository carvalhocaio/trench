from datetime import datetime
from uuid import UUID


class DomainValidationError(ValueError):
    pass


class GameNotStartedError(Exception):
    def __init__(self, game_id: UUID, kickoff: datetime) -> None:
        super().__init__(f"game {game_id} has not started yet (kickoff at {kickoff})")
        self.game_id = game_id
        self.kickoff = kickoff
