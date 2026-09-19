from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.agent.samples import GROUNDED
from trench.api.app import create_app
from trench.api.dependencies import get_preview_writer, get_session
from trench.application.previews import MatchupContext, MatchupPreview
from trench.config import AnalyticsSettings, get_analytics_settings


class StaticPreviewWriter:
    async def write(self, context: MatchupContext) -> MatchupPreview:
        return GROUNDED


@pytest.fixture
def app(session: AsyncSession) -> FastAPI:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session.begin_nested():
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_analytics_settings] = lambda: AnalyticsSettings(
        _env_file=None  # pyright: ignore[reportCallIssue]
    )
    app.dependency_overrides[get_preview_writer] = StaticPreviewWriter
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
