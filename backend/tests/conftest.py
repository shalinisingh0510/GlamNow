"""
Shared test fixtures with in-memory SQLite async database.

Provides hermetic database sessions and in-process async HTTP client.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_db_session
from app.main import create_app

# SQLite in-memory test engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as s:
        yield s


@pytest.fixture
def app(session: AsyncSession):
    """Create application instance with overridden database session."""
    test_app = create_app()

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    test_app.dependency_overrides[get_db_session] = override_get_db_session
    return test_app


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client that talks to the app in-process."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
