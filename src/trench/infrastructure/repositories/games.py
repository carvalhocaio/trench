from uuid import UUID

from sqlalchemy import or_, select

from trench.domain.entities import Game, Score
from trench.infrastructure.models import GameModel
from trench.infrastructure.repositories.base import SqlRepository


class SqlGameRepository(SqlRepository[GameModel, Game]):
    model = GameModel

    @staticmethod
    def to_entity(model: GameModel) -> Game:
        score = (
            None
            if model.home_score is None or model.away_score is None
            else Score(home=model.home_score, away=model.away_score)
        )
        return Game(
            id=model.id,
            season=model.season,
            week=model.week,
            kickoff=model.kickoff,
            home_team_id=model.home_team_id,
            away_team_id=model.away_team_id,
            score=score,
        )

    @staticmethod
    def to_model(entity: Game) -> GameModel:
        return GameModel(
            id=entity.id,
            season=entity.season,
            week=entity.week,
            kickoff=entity.kickoff,
            home_team_id=entity.home_team_id,
            away_team_id=entity.away_team_id,
            home_score=entity.score.home if entity.score else None,
            away_score=entity.score.away if entity.score else None,
        )

    async def get(self, game_id: UUID) -> Game | None:
        return await self._get(game_id)

    async def list_by_season(
        self, season: int, *, week: int | None = None
    ) -> list[Game]:
        query = select(GameModel).where(GameModel.season == season)
        if week is not None:
            query = query.where(GameModel.week == week)
        return await self._fetch(query.order_by(GameModel.kickoff))

    async def list_by_team(self, team_id: UUID, season: int) -> list[Game]:
        query = select(GameModel).where(
            GameModel.season == season,
            or_(GameModel.home_team_id == team_id, GameModel.away_team_id == team_id),
        )
        return await self._fetch(query.order_by(GameModel.kickoff))
