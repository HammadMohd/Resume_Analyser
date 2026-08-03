"""Rate limiting middleware for API protection."""

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

_rate_limit_enabled = True


def disable_rate_limiting() -> None:
    """Disable rate limiting (for testing)."""
    global _rate_limit_enabled
    _rate_limit_enabled = False


def enable_rate_limiting() -> None:
    """Enable rate limiting."""
    global _rate_limit_enabled
    _rate_limit_enabled = True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    def reset(self) -> None:
        """Reset all rate limit counters."""
        self.requests.clear()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, client_ip: str, now: float) -> None:
        """Remove requests older than 1 minute."""
        cutoff = now - 60
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] if req_time > cutoff
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        if not _rate_limit_enabled:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        self._cleanup_old_requests(client_ip, now)

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "detail": f"Max {self.requests_per_minute} requests per minute",
                },
            )

        self.requests[client_ip].append(now)
        return await call_next(request)
