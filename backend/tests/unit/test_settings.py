"""
Tests for the settings module.
"""

from __future__ import annotations

import os

import pytest

from app.core.settings import Environment, Settings


def test_default_settings():
    """Default settings should load without any environment variables."""
    settings = Settings()
    assert settings.environment == Environment.DEVELOPMENT
    assert settings.debug is False
    assert settings.app_name == "GlamNow"
    assert settings.api_prefix == "/api/v1"


def test_is_production():
    """is_production should be True only in production environment."""
    settings = Settings(environment=Environment.PRODUCTION)
    assert settings.is_production is True

    settings = Settings(environment=Environment.DEVELOPMENT)
    assert settings.is_production is False


def test_default_secret_key_warning():
    """Using the default secret key should emit a warning."""
    with pytest.warns(UserWarning, match="default secret key"):
        Settings()


def test_pool_size_bounds():
    """Pool size must be within configured bounds."""
    with pytest.raises(Exception):
        Settings(database_pool_size=0)
    with pytest.raises(Exception):
        Settings(database_pool_size=100)
