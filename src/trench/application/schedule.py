from datetime import datetime
from uuid import UUID

from trench.application.errors import ScheduleConflictError
from trench.application.lookups import require_game, require_team
from trench.domain.entities import Game, Score
from trench.domain.repositories import GameRepository, TeamRepository


class ScheduleService:
    def __init__(self, *, teams: TeamRepository, games: GameRepository) -> None:
        self._teams = teams
        self._games = games

    async def schedule(
        self,
        *,
        season: int,
        week: int,
        kickoff: datetime,
        home_team_id: UUID,
        away_team_id: UUID,
    ) -> Game:
        game = Game(
            season=season,
            week=week,
            kickoff=kickoff,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        )
        for team_id in (home_team_id, away_team_id):
            await require_team(self._teams, team_id)
        await self._require_free_week(game)
        await self._games.save(game)
        return game

    async def record_score(self, game_id: UUID, score: Score) -> Game:
        game = (await self.get(game_id)).finalize(score)
        await self._games.save(game)
        return game

    async def get(self, game_id: UUID) -> Game:
        return await require_game(self._games, game_id)

    async def find(
        self, season: int, *, week: int | None = None, team_id: UUID | None = None
    ) -> list[Game]:
        if team_id is None:
            return await self._games.list_by_season(season, week=week)
        await require_team(self._teams, team_id)
        games = await self._games.list_by_team(team_id, season)
        return [game for game in games if week in (None, game.week)]

    async def _require_free_week(self, game: Game) -> None:
        week_games = await self._games.list_by_season(game.season, week=game.week)
        for team_id in (game.home_team_id, game.away_team_id):
            if any(scheduled.involves(team_id) for scheduled in week_games):
                raise ScheduleConflictError(team_id, game.season, game.week)
