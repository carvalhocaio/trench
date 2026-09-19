from abc import ABC, abstractmethod
from collections.abc import Collection, Hashable, Iterable
from uuid import UUID

from trench.domain.entities import (
    Absence,
    Game,
    Player,
    PlayerGameStats,
    PredictionSnapshot,
    Team,
    TeamGameStats,
)


class InMemoryRepository[KeyT: Hashable, EntityT](ABC):
    def __init__(self) -> None:
        self._items: dict[KeyT, EntityT] = {}

    @abstractmethod
    def key(self, entity: EntityT) -> KeyT: ...

    async def save(self, entity: EntityT, /) -> None:
        self._items[self.key(entity)] = entity

    def all(self) -> list[EntityT]:
        return list(self._items.values())


class FakeTeamRepository(InMemoryRepository[UUID, Team]):
    def key(self, entity: Team) -> UUID:
        return entity.id

    async def get(self, team_id: UUID) -> Team | None:
        return self._items.get(team_id)

    async def get_by_abbreviation(self, abbreviation: str) -> Team | None:
        return next(
            (team for team in self.all() if team.abbreviation == abbreviation), None
        )

    async def list_all(self) -> list[Team]:
        return sorted(self.all(), key=lambda team: team.abbreviation)


class FakeGameRepository(InMemoryRepository[UUID, Game]):
    def key(self, entity: Game) -> UUID:
        return entity.id

    async def get(self, game_id: UUID) -> Game | None:
        return self._items.get(game_id)

    async def list_by_season(
        self, season: int, *, week: int | None = None
    ) -> list[Game]:
        return self._sorted(
            game
            for game in self.all()
            if game.season == season and week in (None, game.week)
        )

    async def list_by_team(self, team_id: UUID, season: int) -> list[Game]:
        return self._sorted(
            game
            for game in self.all()
            if game.season == season and game.involves(team_id)
        )

    def season_of(self, game_id: UUID) -> int:
        return self._items[game_id].season

    @staticmethod
    def _sorted(games: Iterable[Game]) -> list[Game]:
        return sorted(games, key=lambda game: game.kickoff)


class FakePlayerRepository(InMemoryRepository[UUID, Player]):
    def key(self, entity: Player) -> UUID:
        return entity.id

    async def get(self, player_id: UUID) -> Player | None:
        return self._items.get(player_id)

    async def get_many(self, player_ids: Collection[UUID]) -> list[Player]:
        return sorted(
            (self._items[i] for i in set(player_ids) if i in self._items),
            key=lambda player: player.name,
        )

    async def list_by_team(self, team_id: UUID) -> list[Player]:
        return sorted(
            (player for player in self.all() if player.team_id == team_id),
            key=lambda player: (player.position, player.name),
        )


class FakeTeamGameStatsRepository(InMemoryRepository[tuple[UUID, UUID], TeamGameStats]):
    def __init__(self, games: FakeGameRepository) -> None:
        super().__init__()
        self._games = games

    def key(self, entity: TeamGameStats) -> tuple[UUID, UUID]:
        return entity.game_id, entity.team_id

    async def list_by_season(self, season: int) -> list[TeamGameStats]:
        return [
            stats
            for stats in self.all()
            if self._games.season_of(stats.game_id) == season
        ]


class FakePlayerGameStatsRepository(
    InMemoryRepository[tuple[UUID, UUID], PlayerGameStats]
):
    def __init__(self, games: FakeGameRepository) -> None:
        super().__init__()
        self._games = games

    def key(self, entity: PlayerGameStats) -> tuple[UUID, UUID]:
        return entity.game_id, entity.player_id

    async def list_by_season(self, season: int) -> list[PlayerGameStats]:
        return [
            stats
            for stats in self.all()
            if self._games.season_of(stats.game_id) == season
        ]


class FakeAbsenceRepository(InMemoryRepository[tuple[UUID, UUID], Absence]):
    def key(self, entity: Absence) -> tuple[UUID, UUID]:
        return entity.game_id, entity.player_id

    async def remove(self, game_id: UUID, player_id: UUID) -> None:
        self._items.pop((game_id, player_id), None)

    async def list_by_game(self, game_id: UUID) -> list[Absence]:
        return [absence for absence in self.all() if absence.game_id == game_id]


class FakePredictionSnapshotRepository(InMemoryRepository[UUID, PredictionSnapshot]):
    def __init__(self, games: FakeGameRepository) -> None:
        super().__init__()
        self._games = games

    def key(self, entity: PredictionSnapshot) -> UUID:
        return entity.id

    async def list_by_game(self, game_id: UUID) -> list[PredictionSnapshot]:
        return sorted(
            (snapshot for snapshot in self.all() if snapshot.game_id == game_id),
            key=lambda snapshot: snapshot.as_of,
        )

    async def list_by_season(self, season: int) -> list[PredictionSnapshot]:
        return sorted(
            (
                snapshot
                for snapshot in self.all()
                if self._games.season_of(snapshot.game_id) == season
            ),
            key=lambda snapshot: snapshot.as_of,
        )
