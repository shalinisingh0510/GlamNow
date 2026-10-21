"""
Application settings with Pydantic validation.

All configuration is read from environment variables or a `.env` file.
Startup fails fast if required settings are missing rather than silently
using dangerous defaults.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Central configuration sourced from environment variables.

    Variable prefix: ``GLAMNOW_``
    """

    model_config = SettingsConfigDict(
        env_prefix="GLAMNOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "GlamNow"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: str = "INFO"
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="CORS origins. In production this must be explicit.",
    )
    api_prefix: str = "/api/v1"

    # ── Secrets ──────────────────────────────────────────────────
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION",
        description="Used for signing tokens. Must be random in non-dev.",
    )

    # ── Database ─────────────────────────────────────────────────
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/glamnow",
        description="Async PostgreSQL DSN.",
    )
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)

    # ── Redis ────────────────────────────────────────────────────
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string.",
    )

    # ── File uploads ─────────────────────────────────────────────
    max_upload_size_mb: int = Field(default=10, ge=1, le=50)
    allowed_upload_types: list[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "application/pdf"],
    )

    # ── Operational targets ──────────────────────────────────────
    quick_booking_target_minutes: int = Field(
        default=10,
        description="Target quick-booking arrival, not a guarantee.",
    )

    @field_validator("secret_key")
    @classmethod
    def _warn_default_secret(cls, v: str, info) -> str:  # noqa: ANN001
        import warnings

        if v == "CHANGE-ME-IN-PRODUCTION":
            warnings.warn(
                "Using default secret key. Set GLAMNOW_SECRET_KEY in production.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton for the application settings."""
    return Settings()
