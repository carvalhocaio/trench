from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from trench.domain.entities import Game, Score
from trench.infrastructure.models import GameModel


def _to_entity(model: GameModel) -> Game:
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


def _to_model(game: Game) -> GameModel:
    return GameModel(
        id=game.id,
        season=game.season,
        week=game.week,
        kickoff=game.kickoff,
        home_team_id=game.home_team_id,
        away_team_id=game.away_team_id,
        home_score=game.score.home if game.score else None,
        away_score=game.score.away if game.score else None,
    )


class SqlGameRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, game: Game) -> None:
        await self._session.merge(_to_model(game))
        await self._session.flush()

    async def get(self, game_id: UUID) -> Game | None:
        model = await self._session.get(GameModel, game_id)
        return _to_entity(model) if model else None

    async def list_by_season(
        self, season: int, *, week: int | None = None
    ) -> list[Game]:
        query = select(GameModel).where(GameModel.season == season)
        if week is not None:
            query = query.where(GameModel.week == week)
        return await self._fetch(query)

    async def list_by_team(self, team_id: UUID, season: int) -> list[Game]:
        query = select(GameModel).where(
            GameModel.season == season,
            or_(GameModel.home_team_id == team_id, GameModel.away_team_id == team_id),
        )
        return await self._fetch(query)

    async def _fetch(self, query: Select[tuple[GameModel]]) -> list[Game]:
        models = await self._session.scalars(query.order_by(GameModel.kickoff))
        return [_to_entity(model) for model in models]
