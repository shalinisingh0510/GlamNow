"""
Shared test fixtures.

Uses httpx async client to test the FastAPI app without starting
a real server process.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    """Create a fresh application instance per test."""
    return create_app()


@pytest.fixture
async def client(app):
    """Async HTTP client that talks to the app in-process."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
