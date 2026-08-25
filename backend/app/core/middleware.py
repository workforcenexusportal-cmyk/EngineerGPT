"""HTTP middleware: request-id, structured access logging, and rate limiting.

The rate limiter uses Redis when available and degrades gracefully to an
in-process fixed-window counter for local/dev environments.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger("engineergpt.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request id and emit a structured access log line per request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        start = time.perf_counter()
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled_error",
                extra={"extra_fields": {"request_id": request_id, "path": request.url.path}},
            )
            raise
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["x-request-id"] = request_id
        logger.info(
            "request",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                }
            },
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple fixed-window per-client rate limiter (in-process fallback)."""

    def __init__(self, app, limit: int = 120, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        client = request.client.host if request.client else "anonymous"
        now = time.time()
        window_start = now - self.window
        recent = [t for t in self._hits[client] if t > window_start]
        if len(recent) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
            )
        recent.append(now)
        self._hits[client] = recent
        return await call_next(request)
