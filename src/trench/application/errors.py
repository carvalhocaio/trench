from uuid import UUID


class GameNotFoundError(Exception):
    def __init__(self, game_id: UUID) -> None:
        super().__init__(f"game {game_id} not found")
        self.game_id = game_id
