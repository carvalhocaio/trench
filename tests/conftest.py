import asyncio
from collections.abc import AsyncIterator

import pytest
from pydantic_ai import models
from sqlalchemy import URL, pool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from trench.config import get_database_settings
from trench.infrastructure.models import Base

TEST_DATABASE_SUFFIX = "_test"
models.ALLOW_MODEL_REQUESTS = False


async def _prepare_database(url: URL) -> None:
    maintenance = create_async_engine(
        url.set(database="postgres"),
        poolclass=pool.NullPool,
        isolation_level="AUTOCOMMIT",
    )
    async with maintenance.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": url.database},
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    await maintenance.dispose()

    engine = create_async_engine(url, poolclass=pool.NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def database_url() -> URL:
    settings = get_database_settings()
    url = settings.url.set(database=f"{settings.db}{TEST_DATABASE_SUFFIX}")
    asyncio.run(_prepare_database(url))
    return url


@pytest.fixture
async def session(database_url: URL) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(database_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as session:
            yield session
        await transaction.rollback()
    await engine.dispose()
