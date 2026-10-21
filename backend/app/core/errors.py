"""
Structured error types and consistent error response shape.

Every API error response has the same JSON shape so clients can rely
on a single error model regardless of HTTP status code.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Wire-format for a single error."""

    code: str
    message: str
    field: str | None = None
    meta: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Wire-format for all error responses."""

    ok: bool = False
    request_id: str | None = None
    errors: list[ErrorDetail]


class AppError(Exception):
    """
    Base application error that maps to an HTTP response.

    Subclass for domain-specific errors; do not raise raw
    ``HTTPException`` from business logic.
    """

    def __init__(
        self,
        *,
        status_code: int = 400,
        code: str = "BAD_REQUEST",
        message: str = "Something went wrong.",
        field: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = ErrorDetail(code=code, message=message, field=field, meta=meta)
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(
        self,
        resource: str = "Resource",
        identifier: str | None = None,
        message: str | None = None,
    ) -> None:
        if message:
            msg = message
        else:
            msg = f"{resource} not found"
            if identifier:
                msg += f": {identifier}"
        super().__init__(status_code=404, code="NOT_FOUND", message=msg)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict.") -> None:
        super().__init__(status_code=409, code="CONFLICT", message=message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden.") -> None:
        super().__init__(status_code=403, code="FORBIDDEN", message=message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed.", field: str | None = None) -> None:
        super().__init__(status_code=422, code="VALIDATION_ERROR", message=message, field=field)


# ── Exception handlers registered on the FastAPI app ──────────────


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Turn ``AppError`` into a consistent JSON shape."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            request_id=getattr(request.state, "request_id", None),
            errors=[exc.detail],
        ).model_dump(exclude_none=True),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Catch FastAPI / Starlette ``HTTPException`` and normalise."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            request_id=getattr(request.state, "request_id", None),
            errors=[
                ErrorDetail(
                    code=f"HTTP_{exc.status_code}",
                    message=str(exc.detail),
                )
            ],
        ).model_dump(exclude_none=True),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last-resort handler.  Log the real traceback but never expose
    internal details to the caller.
    """
    import logging

    logger = logging.getLogger("glamnow.errors")
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
        extra={"request_id": getattr(request.state, "request_id", None)},
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            request_id=getattr(request.state, "request_id", None),
            errors=[
                ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred. Please try again later.",
                )
            ],
        ).model_dump(exclude_none=True),
    )
