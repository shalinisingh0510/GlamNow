"""
Tests for the error handling module.
"""

from __future__ import annotations

import pytest

from app.core.errors import (
    AppError,
    ConflictError,
    ErrorResponse,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


def test_not_found_error():
    """NotFoundError should produce a 404 with a descriptive message."""
    err = NotFoundError("Service", "srv-123")
    assert err.status_code == 404
    assert err.detail.code == "NOT_FOUND"
    assert "srv-123" in err.detail.message


def test_conflict_error():
    """ConflictError should produce a 409."""
    err = ConflictError("Booking already exists.")
    assert err.status_code == 409
    assert err.detail.code == "CONFLICT"


def test_forbidden_error():
    """ForbiddenError should produce a 403."""
    err = ForbiddenError()
    assert err.status_code == 403


def test_unauthorized_error():
    """UnauthorizedError should produce a 401."""
    err = UnauthorizedError()
    assert err.status_code == 401


def test_validation_error_with_field():
    """ValidationError should carry a field name when provided."""
    err = ValidationError("Invalid duration.", field="duration_minutes")
    assert err.detail.field == "duration_minutes"
    assert err.status_code == 422


def test_error_response_shape():
    """ErrorResponse model should serialise correctly."""
    resp = ErrorResponse(
        request_id="req-abc",
        errors=[AppError(code="TEST", message="Test error").detail],
    )
    data = resp.model_dump(exclude_none=True)
    assert data["ok"] is False
    assert data["request_id"] == "req-abc"
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "TEST"


@pytest.mark.asyncio
async def test_app_error_returns_structured_json(client):
    """Raising AppError from an endpoint should produce structured JSON."""
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/test-error")
    async def trigger_error():
        raise NotFoundError("TestResource", "test-1")

    # Inject the test route
    client._transport.app.include_router(router, prefix="/api/v1")

    response = await client.get("/api/v1/test-error")
    assert response.status_code == 404
    data = response.json()
    assert data["ok"] is False
    assert data["errors"][0]["code"] == "NOT_FOUND"
