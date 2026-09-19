from uuid import UUID


class NotFoundError(Exception):
    resource: str

    def __init__(self, resource_id: UUID) -> None:
        super().__init__(f"{self.resource} {resource_id} not found")
        self.resource_id = resource_id


class GameNotFoundError(NotFoundError):
    resource = "game"


class TeamNotFoundError(NotFoundError):
    resource = "team"


class PlayerNotFoundError(NotFoundError):
    resource = "player"


class TeamNotInGameError(Exception):
    def __init__(self, team_id: UUID, game_id: UUID) -> None:
        super().__init__(f"team {team_id} does not play in game {game_id}")
        self.team_id = team_id
        self.game_id = game_id


class ScheduleConflictError(Exception):
    def __init__(self, team_id: UUID, season: int, week: int) -> None:
        super().__init__(f"team {team_id} already plays in week {week} of {season}")
        self.team_id = team_id
