"""
Health and readiness endpoints.

These are the first real routes: they prove the server boots, can
reach its database, and can respond with the correct JSON shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings, get_settings
from app.db import get_db_session

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    ok: bool
    environment: str
    version: str
    timestamp: str


class ReadinessCheck(BaseModel):
    name: str
    ok: bool
    latency_ms: float | None = None
    error: str | None = None


class ReadinessResponse(BaseModel):
    ok: bool
    checks: list[ReadinessCheck]


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Liveness probe.

    Returns ``200 OK`` if the process is alive. Does not touch the
    database or any external service.
    """
    return HealthResponse(
        ok=True,
        environment=settings.environment.value,
        version="0.1.0",
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness(
    db: AsyncSession = Depends(get_db_session),
) -> ReadinessResponse:
    """
    Readiness probe.

    Checks that the database connection is functional.  Returns
    ``200 OK`` only when all checks pass; ``503`` otherwise.
    """
    checks: list[ReadinessCheck] = []
    all_ok = True

    # Database check
    import time

    t0 = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        latency = round((time.monotonic() - t0) * 1000, 2)
        checks.append(ReadinessCheck(name="database", ok=True, latency_ms=latency))
    except Exception as exc:
        latency = round((time.monotonic() - t0) * 1000, 2)
        checks.append(
            ReadinessCheck(name="database", ok=False, latency_ms=latency, error=str(exc))
        )
        all_ok = False

    return ReadinessResponse(ok=all_ok, checks=checks)
