from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from trench.api.app import create_app
from trench.api.dependencies import get_session


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session.begin_nested():
            yield session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
