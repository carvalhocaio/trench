from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from trench import __version__
from trench.api.errors import register_exception_handlers
from trench.api.routes import games, health, teams
from trench.config import get_database_settings
from trench.infrastructure.database import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_engine(get_database_settings())
    app.state.session_factory = create_session_factory(engine)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Trench", version=__version__, lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(teams.router)
    app.include_router(games.router)
    return app
