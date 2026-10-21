"""
Request-ID middleware.

Assigns a unique ``X-Request-ID`` to every inbound request and stores
it in ``request.state.request_id`` for use in logs and error responses.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Attach a request ID from the ``X-Request-ID`` header, or generate one.

    The ID is always returned in the response headers so callers can
    correlate responses with their requests.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
