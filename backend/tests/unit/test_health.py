"""
Tests for the health and readiness endpoints.

These verify the foundation: the app boots, responds with the correct
shape, and reports its environment.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    """Health endpoint should return 200 with environment info."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "environment" in data
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_response_shape(client):
    """Health response must contain exactly the expected fields."""
    response = await client.get("/api/v1/health")
    data = response.json()
    expected_keys = {"ok", "environment", "version", "timestamp"}
    assert set(data.keys()) == expected_keys


@pytest.mark.asyncio
async def test_request_id_header_generated(client):
    """Every response must include an X-Request-ID header."""
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_request_id_header_echoed(client):
    """When the caller supplies X-Request-ID, the same value is echoed."""
    custom_id = "test-correlation-12345"
    response = await client.get(
        "/api/v1/health",
        headers={"X-Request-ID": custom_id},
    )
    assert response.headers["x-request-id"] == custom_id


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client):
    """Unknown routes should return 404 status."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    data = response.json()
    # FastAPI's default 404 is caught by our http_exception_handler
    # which wraps it in the ErrorResponse shape
    assert "errors" in data or "detail" in data
