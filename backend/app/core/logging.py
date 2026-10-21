"""
Structured JSON logging with redaction of sensitive fields.

Passwords, tokens, payment secrets, private measurements, and
other sensitive data must never appear in log output.
"""

from __future__ import annotations

import logging
import sys
from typing import Any


# Fields whose values are replaced with ``"***"`` before logging.
REDACTED_FIELDS: frozenset[str] = frozenset(
    {
        "password",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "payment_secret",
        "card_number",
        "cvv",
        "measurement",
        "measurements",
    }
)


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    """Shallow-redact known sensitive keys."""
    return {
        k: "***" if k.lower() in REDACTED_FIELDS else v
        for k, v in data.items()
    }


class JSONFormatter(logging.Formatter):
    """
    Emit one JSON object per log line.

    Includes ``request_id`` and ``extra`` fields when present.
    """

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        payload: dict[str, Any] = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1]:
            payload["exception"] = self.formatException(record.exc_info)
        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord("", 0, "", 0, None, None, None).__dict__
            and k not in ("message", "request_id")
        }
        if extra:
            payload["extra"] = _redact(extra)
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging with JSON output to stderr."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()
    root.addHandler(handler)
    # Reduce noise from dependency loggers
    for quiet in ("uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
        logging.getLogger(quiet).setLevel(logging.WARNING)
