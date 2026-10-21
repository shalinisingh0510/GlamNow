"""
FastAPI application composition and lifespan.

This is the single entry point that wires up middleware, exception
handlers, routers, and lifecycle hooks.  Business logic lives in
modules — this file only composes them.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.core.settings import get_settings
from app.db import dispose_engine

logger = logging.getLogger("glamnow.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan.

    Setup runs before the first request; teardown runs on shutdown.
    """
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info(
        "Starting %s in %s mode",
        settings.app_name,
        settings.environment.value,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)
    await dispose_engine()


def create_app() -> FastAPI:
    """Application factory — called once per process."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Quick commerce for at-home beauty, grooming, tailoring and wellness services.",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware (outermost first) ──────────────────────────────
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ── Exception handlers ───────────────────────────────────────
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Routers ──────────────────────────────────────────────────
    from app.api.v1.health import router as health_router

    app.include_router(health_router, prefix=settings.api_prefix)

    return app


# Module-level instance for ``uvicorn app.main:app``
app = create_app()
